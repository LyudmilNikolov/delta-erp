import os
import shutil
import time
import uuid
import logging

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from excel_processing import ProcessingError, dataframe_to_records, process_source


app = FastAPI(title="Delta ERP Backend")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
DEFAULT_OUTPUT_TTL_SECONDS = 24 * 60 * 60
DEFAULT_ALLOWED_ORIGINS = ("http://localhost:4200", "http://127.0.0.1:4200")
ALLOWED_EXTENSIONS = {".xls", ".xlsx"}

os.makedirs(OUTPUT_DIR, exist_ok=True)


def _output_ttl_seconds() -> int:
    raw_value = os.getenv("OUTPUT_TTL_SECONDS")
    if raw_value is None:
        return DEFAULT_OUTPUT_TTL_SECONDS
    try:
        return max(0, int(raw_value))
    except ValueError:
        logger.warning("Invalid OUTPUT_TTL_SECONDS value: %s", raw_value)
        return DEFAULT_OUTPUT_TTL_SECONDS


OUTPUT_TTL_SECONDS = _output_ttl_seconds()


def _allowed_origins() -> list[str]:
    origins = os.getenv("CORS_ALLOWED_ORIGINS")
    if origins is None:
        return list(DEFAULT_ALLOWED_ORIGINS)
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


allowed_origins = _allowed_origins()
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )


def api_error(message: str, status_code: int) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status_code)


def cleanup_expired_outputs(now: float | None = None) -> None:
    if OUTPUT_TTL_SECONDS <= 0 or not os.path.isdir(OUTPUT_DIR):
        return

    cutoff = (now if now is not None else time.time()) - OUTPUT_TTL_SECONDS
    for filename in os.listdir(OUTPUT_DIR):
        path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.isfile(path):
            continue
        try:
            if os.path.getmtime(path) < cutoff:
                os.remove(path)
        except OSError:
            logger.warning(
                "Could not remove expired output file: %s",
                path,
                exc_info=True,
            )


def _remove_file(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        logger.warning("Could not remove file: %s", path, exc_info=True)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    _request: Request,
    _exc: RequestValidationError,
) -> JSONResponse:
    return api_error(
        "Invalid request. Upload exactly one Excel file in the 'file' form field.",
        400,
    )


@app.post("/process")
async def process_excel(
    files: list[UploadFile] = File(..., alias="file"),
    sheet_name: str | None = Form(default=None),
):
    cleanup_expired_outputs()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if len(files) != 1:
        for upload in files:
            await upload.close()
        return api_error("Upload exactly one Excel file.", 400)

    file = files[0]
    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        await file.close()
        return api_error("Only .xls and .xlsx files are supported.", 400)

    upload_filename = f"{uuid.uuid4()}{extension}"
    upload_path = os.path.join(OUTPUT_DIR, upload_filename)
    result_filename = f"{uuid.uuid4()}.xlsx"
    result_path = os.path.join(OUTPUT_DIR, result_filename)

    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = process_source(
            upload_path,
            sheet_name=sheet_name or None,
            result_path=result_path,
        )
    except ProcessingError as exc:
        _remove_file(result_path)
        return api_error(str(exc), 400)
    except Exception:
        logger.exception("Unexpected error while processing uploaded Excel file.")
        _remove_file(result_path)
        return api_error("Unexpected processing error.", 500)
    finally:
        _remove_file(upload_path)
        await file.close()

    return {
        "sheet_name": result["sheet_name"],
        "row_count": len(result["details"]),
        "excel_file": f"/download/{result_filename}",
        "seasoned_terms": result["seasoned_terms"],
        "warnings": result["warnings"],
        "details": dataframe_to_records(result["details"]),
        "sheet1": dataframe_to_records(result["sheet1"]),
        "pivots": {
            "seasoned": dataframe_to_records(result["seasoned_pivot"]),
            "all_kg": dataframe_to_records(result["all_kg_pivot"]),
        },
    }


@app.post("/process/")
async def process_excel_with_trailing_slash(
    files: list[UploadFile] = File(..., alias="file"),
    sheet_name: str | None = Form(default=None),
):
    return await process_excel(files=files, sheet_name=sheet_name)


@app.get("/download/{filename:path}")
async def download_file(filename: str):
    cleanup_expired_outputs()

    safe_filename = os.path.basename(filename)
    if safe_filename != filename:
        return api_error("Invalid filename.", 400)

    path = os.path.join(OUTPUT_DIR, safe_filename)
    if os.path.exists(path):
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=safe_filename,
        )
    return api_error("File not found.", 404)

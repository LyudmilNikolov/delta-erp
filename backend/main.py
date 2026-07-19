import os
import re
import shutil
import sys
import time
import uuid
import logging
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from excel_processing import ProcessingError, dataframe_to_records, process_source


app = FastAPI(title="Delta ERP Backend")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent


def _web_dir() -> Path:
    configured_dir = os.getenv("DELTA_ERP_WEB_DIR")
    if configured_dir:
        return Path(configured_dir).resolve()
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "web"
    return BASE_DIR.parent / "frontend" / "dist" / "delta-erp" / "browser"


def _output_dir() -> Path:
    configured_dir = os.getenv("DELTA_ERP_DATA_DIR")
    if configured_dir:
        return Path(configured_dir).expanduser().resolve() / "outputs"
    if getattr(sys, "frozen", False):
        app_data = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        data_root = Path(app_data) if app_data else Path.home() / ".delta-erp"
        return data_root / "DeltaERP" / "outputs"
    return BASE_DIR / "outputs"


WEB_DIR = _web_dir()
OUTPUT_DIR = str(_output_dir())
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


def _source_filename(filename: str | None) -> str:
    return os.path.basename((filename or "workbook.xlsx").replace("\\", "/"))


def _result_filename(source_filename: str) -> str:
    source_stem = os.path.splitext(source_filename)[0]
    safe_stem = re.sub(r"[^\w.-]+", "_", source_stem).strip("._")[:80]
    return f"Резултат_{safe_stem or 'файл'}_{uuid.uuid4().hex[:8]}.xlsx"


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    _request: Request,
    _exc: RequestValidationError,
) -> JSONResponse:
    return api_error(
        "Невалидна заявка. Изберете точно един Excel файл.",
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
        return api_error("Изберете точно един Excel файл.", 400)

    file = files[0]
    source_filename = _source_filename(file.filename)
    extension = os.path.splitext(source_filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        await file.close()
        return api_error("Поддържат се само файлове във формат .xls и .xlsx.", 400)

    upload_filename = f"{uuid.uuid4()}{extension}"
    upload_path = os.path.join(OUTPUT_DIR, upload_filename)
    result_filename = _result_filename(source_filename)
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
        return api_error("Възникна неочаквана грешка при обработката.", 500)
    finally:
        _remove_file(upload_path)
        await file.close()

    return {
        "source_filename": source_filename,
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
        return api_error("Невалидно име на файл.", 400)

    path = os.path.join(OUTPUT_DIR, safe_filename)
    if os.path.exists(path):
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=safe_filename,
        )
    return api_error("Файлът не е намерен.", 404)


@app.get("/{frontend_path:path}", include_in_schema=False)
async def serve_frontend(frontend_path: str):
    index_path = WEB_DIR / "index.html"
    if not index_path.is_file():
        return api_error("Потребителският интерфейс не е инсталиран.", 404)

    requested_path = (WEB_DIR / frontend_path).resolve()
    try:
        requested_path.relative_to(WEB_DIR.resolve())
    except ValueError:
        return api_error("Невалиден път.", 400)

    if frontend_path and requested_path.is_file():
        return FileResponse(requested_path)
    if not Path(frontend_path).suffix:
        return FileResponse(index_path)
    return api_error("Файлът не е намерен.", 404)

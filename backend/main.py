import os
import shutil
import uuid

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from excel_processing import ProcessingError, dataframe_to_records, process_source


app = FastAPI(title="Delta ERP Backend")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.post("/process")
async def process_excel(
    file: UploadFile = File(...),
    sheet_name: str | None = Form(default=None),
):
    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in {".xls", ".xlsx"}:
        return JSONResponse(
            {"error": "Only .xls and .xlsx files are supported."},
            status_code=400,
        )

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
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
    finally:
        if os.path.exists(upload_path):
            os.remove(upload_path)

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
    file: UploadFile = File(...),
    sheet_name: str | None = Form(default=None),
):
    return await process_excel(file=file, sheet_name=sheet_name)


@app.get("/download/{filename}")
async def download_file(filename: str):
    safe_filename = os.path.basename(filename)
    if safe_filename != filename:
        return JSONResponse({"error": "Invalid filename."}, status_code=400)

    path = os.path.join(OUTPUT_DIR, safe_filename)
    if os.path.exists(path):
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=safe_filename,
        )
    return JSONResponse({"error": "File not found"}, status_code=404)


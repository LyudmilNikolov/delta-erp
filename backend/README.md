# Delta ERP Backend

FastAPI service for processing Microinvest Excel exports.

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

The local API runs at `http://localhost:8000`.

## API Contract

### `POST /process`

Multipart form upload:

- `file`: exactly one `.xls` or `.xlsx` file.
- `sheet_name`: optional sheet name override.

Successful responses include:

- `source_filename`
- `sheet_name`
- `row_count`
- `excel_file`
- `seasoned_terms`
- `warnings`
- `details`
- `sheet1`
- `pivots.seasoned`
- `pivots.all_kg`

Errors use:

```json
{ "error": "Message for the frontend to display." }
```

### `GET /download/{filename}`

Downloads a generated Excel file returned by `excel_file`.

## Configuration

- `CORS_ALLOWED_ORIGINS`: comma-separated frontend origins. Defaults to `http://localhost:4200,http://127.0.0.1:4200`.
- `OUTPUT_TTL_SECONDS`: generated file retention window in seconds. Defaults to `86400`. Set to `0` to disable cleanup.

## Frontend Integration Notes

- Submit one file with multipart `POST http://localhost:8000/process`.
- Use form field `file` for the Excel file.
- Include `sheet_name` only when the UI exposes sheet selection.
- Render backend errors from the response `error` field.
- Use `excel_file` from the response as the download path.

## Tests

```bash
cd backend
pytest
```

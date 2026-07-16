import io
import os
import sys
import time
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main


EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.fixture()
def output_dir(tmp_path, monkeypatch):
    path = tmp_path / "outputs"
    path.mkdir()
    monkeypatch.setattr(main, "OUTPUT_DIR", str(path))
    monkeypatch.setattr(main, "OUTPUT_TTL_SECONDS", 24 * 60 * 60)
    return path


@pytest.fixture()
def client(output_dir):
    with TestClient(main.app) as test_client:
        yield test_client


def _excel_bytes(
    sheet_name: str = "Microinvest",
    valid: bool = True,
    product_name: str = "Кайма 500 гр",
    unit: str = "бр",
) -> bytes:
    if valid:
        df = pd.DataFrame(
            [
                {
                    "Дата": "01.05.2026",
                    "Код": 123,
                    "Стока": product_name,
                    "Група": "Стоки",
                    "Партида": "BATCH-1",
                    "Количество": 2,
                    "Мярка": unit,
                    "Документ №": "DOC-1",
                    "Партньор": "Partner",
                    "Група.1": "Partner group",
                    "Обект": "Site",
                    "Потребител": "User",
                    "Операция": "Sale",
                }
            ]
        )
    else:
        df = pd.DataFrame([{"Wrong": "value"}])

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return buffer.getvalue()


def _post_excel(client: TestClient, content: bytes, filename: str = "input.xlsx", data=None):
    return client.post(
        "/process",
        data=data,
        files={"file": (filename, content, EXCEL_MIME)},
    )


def test_process_valid_excel_returns_payload_and_download(client):
    response = _post_excel(client, _excel_bytes())

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_filename"] == "input.xlsx"
    assert payload["sheet_name"] == "Microinvest"
    assert payload["row_count"] == 1
    assert payload["details"][0]["stock_type"] == "стока"
    assert payload["sheet1"][0]["вид"] == "стока"
    assert payload["excel_file"].startswith("/download/Резултат_input_")
    assert payload["excel_file"].endswith(".xlsx")
    assert isinstance(payload["warnings"], list)
    assert len(payload["details"]) == 1
    assert len(payload["sheet1"]) == 1
    assert set(payload["pivots"]) == {"seasoned", "all_kg"}

    download_response = client.get(payload["excel_file"])

    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == EXCEL_MIME
    assert download_response.content


def test_process_returns_structured_warnings(client):
    response = _post_excel(client, _excel_bytes(unit="литър"))

    assert response.status_code == 200
    assert response.json()["warnings"] == [
        {
            "row": 2,
            "message": "Неподдържана мерна единица „литър“.",
            "product_name": "Кайма 500 гр",
        }
    ]


def test_process_rejects_invalid_extension(client):
    response = _post_excel(client, b"not an excel file", filename="input.txt")

    assert response.status_code == 400
    assert response.json() == {
        "error": "Поддържат се само файлове във формат .xls и .xlsx."
    }


def test_process_rejects_bad_sheet_name(client):
    response = _post_excel(
        client,
        _excel_bytes(),
        data={"sheet_name": "MissingSheet"},
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Листът „MissingSheet“ не е намерен."}


def test_process_rejects_bad_input_shape(client):
    response = _post_excel(client, _excel_bytes(valid=False))

    assert response.status_code == 400
    assert "задължителните колони от Microinvest" in response.json()["error"]


def test_process_rejects_multiple_files(client):
    response = client.post(
        "/process",
        files=[
            ("file", ("first.xlsx", _excel_bytes(), EXCEL_MIME)),
            ("file", ("second.xlsx", _excel_bytes(), EXCEL_MIME)),
        ],
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Изберете точно един Excel файл."}


def test_download_rejects_unsafe_filename(client):
    response = client.get("/download/nested/file.xlsx")

    assert response.status_code == 400
    assert response.json() == {"error": "Невалидно име на файл."}


def test_download_returns_404_for_missing_file(client):
    response = client.get("/download/missing.xlsx")

    assert response.status_code == 404
    assert response.json() == {"error": "Файлът не е намерен."}


def test_cors_allows_local_frontend_origin(client):
    response = client.options(
        "/process",
        headers={
            "origin": "http://localhost:4200",
            "access-control-request-method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:4200"


def test_cleanup_removes_expired_outputs(output_dir, monkeypatch):
    old_output = output_dir / "old.xlsx"
    old_output.write_bytes(b"old")
    now = time.time()
    os.utime(old_output, (now - 10, now - 10))
    monkeypatch.setattr(main, "OUTPUT_TTL_SECONDS", 1)

    main.cleanup_expired_outputs(now=now)

    assert not old_output.exists()

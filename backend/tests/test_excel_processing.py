import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from excel_processing import (
    _format_excel_identifier,
    build_pivot,
    build_sheet1,
    classify_group,
    infer_product_type,
    normalize_microinvest,
    parse_package_weight_kg,
    read_microinvest_sheet,
)


def _source_row(code):
    return {
        "Дата": "27.07.2026",
        "Код": code,
        "Стока": "Тестов продукт",
        "Група": "02 ПУЕШКО",
        "Партида": "B-1",
        "Количество": 1,
        "Мярка": "кг.",
    }


@pytest.mark.parametrize(
    ("description", "expected_kg"),
    [
        ("Наденички, 20 по 40 гр, опаковка 0,800 кг", 0.8),
        ("Кюфтета 0,480/6 бр по 80 гр", 0.48),
        ("Стек, 2 по 0.250", 0.5),
        ("Кюфтета 80 гр, 10 бр в тарелка", 0.08),
    ],
)
def test_parse_package_weight_uses_the_whole_package(description, expected_kg):
    assert parse_package_weight_kg(description) == pytest.approx(expected_kg)


@pytest.mark.parametrize(
    ("description", "expected_type"),
    [
        ("Пуешко месо за готвене окрехкотено", "мг окр"),
        ("Пуешка пържола от бут окрехкотена", "пб окр"),
        ("Пуешко филе окрехкотено", "филе окр"),
        ("Шницел от филе овкусен с билки", "шницел овк"),
        ("Мини шиш с мед и горчица", "шиш мед"),
        ("Стек от горен бут с билки", "горен билки"),
        ("Стек с мед и горчица", "стек мед"),
        ("Обезкостен бут, овкусен с билки", "стек билки"),
        ("Стек от обезкостена плешка", "плешка"),
        ("Кюфтета селски", "селско"),
        ("Наденички пуешки", "наденица"),
        ("Наденички средиземноморски", "средиземн"),
        ("Пилешко филе замразено", "филе пилешко"),
        ("Пуешка подбедрица замразена", "подбедрица"),
        ("Пуешко долно бутче", "дб"),
        ("Пуешки стек спеър рибс", "спеър рибс"),
        ("Пуешки стек с трюфел", "трюфел"),
    ],
)
def test_infer_product_type_matches_manual_categories(description, expected_type):
    assert infer_product_type(description) == expected_type


@pytest.mark.parametrize(
    ("group", "expected_type"),
    [
        ("04 СТОКИ АМАДОРИ/4.2 ЛИДЛ СТОКИ", "стоки"),
        ("06 ПАТЕШКО/ПАТЕШКО ЗАМРАЗЕНО", "стоки"),
        ("02 ПУЕШКО/2.1 ОБЕЗКОСТЕН БУТ", "произв"),
    ],
)
def test_classify_group_matches_manual_stock_rules(group, expected_type):
    assert classify_group(group) == expected_type


@pytest.mark.parametrize(
    ("value", "number_format", "expected"),
    [
        (7, "000000", "000007"),
        (812, "00000", "00812"),
        (123456, "00000", "123456"),
        ("00123", "General", "00123"),
        (4101, "General", "4101"),
    ],
)
def test_format_excel_identifier_uses_the_cell_format(
    value,
    number_format,
    expected,
):
    assert _format_excel_identifier(value, number_format) == expected


def test_read_microinvest_sheet_preserves_displayed_code_values(tmp_path):
    source = pd.DataFrame(
        [
            _source_row(code=7),
            _source_row(code=812),
            _source_row(code=4101),
            _source_row(code="000042"),
        ]
    )
    source_path = tmp_path / "formatted-codes.xlsx"
    with pd.ExcelWriter(source_path, engine="openpyxl") as writer:
        source.to_excel(writer, sheet_name="Microinvest", startrow=2, index=False)

    from openpyxl import load_workbook

    workbook = load_workbook(source_path)
    worksheet = workbook["Microinvest"]
    code_column = list(source.columns).index("Код") + 1
    worksheet.cell(row=4, column=code_column).number_format = "000000"
    worksheet.cell(row=5, column=code_column).number_format = "00000"
    workbook.save(source_path)

    _, result = read_microinvest_sheet(str(source_path))

    assert result["Код"].tolist() == ["000007", "00812", "4101", "000042"]


def test_normalize_applies_identifiers_classification_and_weights():
    source = pd.DataFrame(
        [
            {
                "Дата": "27.07.2026",
                "Код": 1001,
                "Стока": "Пуешки шиш овкусен",
                "Група": "02 ПУЕШКО",
                "Партида": None,
                "Количество": 2,
                "Мярка": "кг.",
                "Група.1": "ТЕСТОВА ГРУПА",
            },
            {
                "Дата": "27.07.2026",
                "Код": 1002,
                "Стока": "Цяло пилешко бутче",
                "Група": "03 ПИЛЕ ЦАРЕВИЧНО/3.2 БУТ",
                "Партида": "B-1",
                "Количество": 100,
                "Мярка": "кг.",
                "Група.1": "ТЕСТОВА ГРУПА",
            },
            {
                "Дата": "27.07.2026",
                "Код": 1003,
                "Стока": "Филе без кожа патешко замразено",
                "Група": "06 ПАТЕШКО/ПАТЕШКО ЗАМРАЗЕНО",
                "Партида": "D-1",
                "Количество": 12,
                "Мярка": "кг.",
                "Група.1": "КЛИЕНТИ",
            },
            {
                "Дата": "27.07.2026",
                "Код": 1004,
                "Стока": "Пилешко филе замразено",
                "Група": "03 ПИЛЕ ЦАРЕВИЧНО",
                "Партида": "F-1",
                "Количество": 3,
                "Мярка": "кг.",
                "Група.1": "КЛИЕНТИ",
            },
            {
                "Дата": "27.07.2026",
                "Код": 1005,
                "Стока": "Пуешки стек овкусен, 2 по 0.250",
                "Група": "02 ПУЕШКО",
                "Партида": "S-1",
                "Количество": 4,
                "Мярка": "бр.",
                "Група.1": "КЛИЕНТИ",
            },
        ]
    )

    normalized, warnings = normalize_microinvest(source)

    assert warnings == []
    assert normalized["code"].tolist() == [
        "1001",
        "1002",
        "1003",
        "1004",
        "1005",
    ]
    assert normalized["batch"].tolist() == ["NA", "B-1", "D-1", "F-1", "S-1"]
    assert normalized["stock_type"].tolist() == [
        "произв",
        "произв",
        "стоки",
        "произв",
        "произв",
    ]
    assert normalized["weight_kg"].tolist() == pytest.approx([2, 100, 12, 3, 2])


def test_summaries_match_manual_scope_and_sorting():
    normalized = pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2026-07-27"),
                "code": "1001",
                "product_name": "Шиш",
                "stock_type": "произв",
                "batch": "B-1",
                "product_type": "шиш",
                "weight_kg": 2.0,
                "is_seasoned_or_ground": True,
            },
            {
                "date": pd.Timestamp("2026-07-27"),
                "code": "2001",
                "product_name": "Патешко филе",
                "stock_type": "стоки",
                "batch": "D-1",
                "product_type": "филе",
                "weight_kg": 12.0,
                "is_seasoned_or_ground": False,
            },
            {
                "date": pd.Timestamp("2026-07-27"),
                "code": "3001",
                "product_name": "Бургер",
                "stock_type": "произв",
                "batch": "B-2",
                "product_type": "бургер",
                "weight_kg": 3.0,
                "is_seasoned_or_ground": True,
            },
        ]
    )

    sheet1 = build_sheet1(normalized)
    seasoned = build_pivot(normalized, seasoned_only=True)
    all_kg = build_pivot(normalized, seasoned_only=False)

    assert sheet1["Код"].tolist() == ["1001", "2001", "3001"]
    assert sheet1["вид"].tolist() == ["произв", "стоки", "произв"]
    assert seasoned[["Партида", "вид", "Total"]].to_dict("records") == [
        {"Партида": "B-1", "вид": "шиш", "Total": 2.0},
        {"Партида": "B-2", "вид": "бургер", "Total": 3.0},
    ]
    assert all_kg[["Партида", "вид", "Total"]].to_dict("records") == [
        {"Партида": "B-1", "вид": "шиш", "Total": 2.0},
        {"Партида": "B-2", "вид": "бургер", "Total": 3.0},
    ]

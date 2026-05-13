import tkinter as tk
from tkinter import filedialog, Tk
import pandas as pd
import json
import uuid
import os
import re


def process_excel_file(file_path: str, query: str):
    df = pd.read_excel(file_path)

    # Apply query logic
    lines = query.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("head:"):
            try:
                n = int(line[len("head:"):])
                df = df.head(n)
            except:
                pass

    # Add UUID
    df.insert(0, "uuid", [str(uuid.uuid4()) for _ in range(len(df))])

    # Convert integer columns to string
    for col in df.columns:
        if pd.api.types.is_integer_dtype(df[col]):
            df[col] = df[col].astype(str)

    return df.astype(str).to_dict(orient="records")

def test_excel_json_generation():
    root = tk.Tk()
    root.withdraw()  # Hide main window

    file_path = filedialog.askopenfilename(
        title="Select Excel file",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )

    if not file_path:
        print("No file selected.")
        return

    query = """
    head:20
    """

    print(f"📂 Selected file: {file_path}")
    print(f"🧠 Running query:\n{query.strip()}\n")

    result = process_excel_file(file_path, query)

    # Create output file path
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    json_path = os.path.join(os.path.dirname(file_path), f"{base_name}_output.json")

    # Write to JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ JSON written to: {json_path}")



def parse_weight_and_count(desc: str) -> float:
    """
    Given a description like:
    'КЮФТЕТА СЕЛСКИ ПУЕШКИ ОХЛАДЕНИ ПО 80 гр-... (240 бр.)',
    extract per-item weight (in grams) and count, then return total weight in kg.
    """
    # Extract weight in grams
    w_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*гр", desc)
    if not w_match:
        return None
    weight_g = float(w_match.group(1).replace(',', '.'))
    # Extract count
    c_match = re.search(r"\((\d+)\s*бр\.\)", desc)
    if not c_match:
        return None
    count = int(c_match.group(1))
    # Total weight in kg
    total_kg = (weight_g * count) / 1000.0
    return total_kg


def process_source(
    source_path: str,
    sheet_name: str = 0,
    date_col: str = 'Дата',
    code_col: str = 'Код',
    desc_col: str = 'Стока',
    type_col: str = 'вид',
    partner_col: str = 'Партньор',
    total_col: str = 'Total',
    result_path: str = 'Processed_Result.xlsx'
) -> dict:
    """
    Reads the source Excel file, converts all items to weight in kg,
    preserves the Партньор (partner) column, builds pivot tables,
    writes the finished Excel file, and returns DataFrames and pivots.

    Returns:
        {
            'df': DataFrame,          # cleaned detailed data including Partner
            'pivot_by_date': DataFrame,
            'pivot_by_type': DataFrame
        }
    """
    # Read source
    df = pd.read_excel(source_path, sheet_name=sheet_name, engine='xlrd')

    # Ensure total weight column exists
    if total_col not in df.columns:
        df[total_col] = pd.NA
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce')

    # Compute missing weights from description
    mask = df[total_col].isna() | (df[total_col] == 0)
    df.loc[mask, total_col] = df.loc[mask, desc_col].apply(parse_weight_and_count)

    # Rename columns, including Партньор to Partner
    df = df.rename(columns={
        date_col: 'Date',
        code_col: 'Code',
        desc_col: 'Description',
        type_col: 'Type',
        partner_col: 'Partner',
        total_col: 'Weight_kg'
    })

    # Normalize Date column
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='ignore')

    # Build pivot tables
    pivot_by_date = df.pivot_table(
        index='Date', values='Weight_kg', aggfunc='sum'
    ).reset_index()

    pivot_by_type = df.pivot_table(
        index='Type', values='Weight_kg', aggfunc='sum'
    ).reset_index()

    # Write to Excel
    with pd.ExcelWriter(result_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Details', index=False)
        pivot_by_date.to_excel(writer, sheet_name='Pivot_by_Date', index=False)
        pivot_by_type.to_excel(writer, sheet_name='Pivot_by_Type', index=False)

    return {
        'df': df,
        'pivot_by_date': pivot_by_date,
        'pivot_by_type': pivot_by_type
    }


if __name__ == '__main__':
    # Interactive file selection for debugging

    root = Tk()
    root.withdraw()  # Hide the main window
    source_file = filedialog.askopenfilename(
        title='Select source Excel file',
        filetypes=[('Excel files', '*.xls *.xlsx'), ('All files', '*.*')]
    )
    if source_file:
        result = process_source(source_file)
        print(f"Processing complete. Output written to default path (Processed_Result.xlsx).")
        # Optionally, inspect DataFrame heads
        print(result['df'].head())




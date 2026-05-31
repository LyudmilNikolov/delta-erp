export interface ProcessedExcelResponse {
  sheet_name: string;
  row_count: number;
  excel_file: string;
  seasoned_terms: {
    ground_meats: string[];
    seasoned: string[];
  };
  warnings: string[];
  details: DetailRow[];
  sheet1: SheetSummaryRow[];
  pivots: {
    seasoned: PivotRow[];
    all_kg: PivotRow[];
  };
  sample_note?: string;
}

export interface DetailRow {
  date: string;
  code: string;
  product_name: string;
  group: string;
  stock_type: string;
  batch: string;
  quantity: number;
  unit: string;
  weight_kg: number;
  product_type: string;
  is_seasoned_or_ground: boolean;
  document_no: string;
  partner: string;
  partner_group: string;
  site: string;
  user: string;
  operation: string;
  original: Record<string, string | number | null>;
}

export interface SheetSummaryRow {
  Дата: string;
  Код: string;
  Стока: string;
  вид: string;
  Total: number;
}

export interface PivotRow {
  Партида: string;
  вид: string;
  Total: number;
}

export interface TableColumn<T> {
  key: keyof T & string;
  label: string;
  type?: 'text' | 'number' | 'date' | 'boolean';
}

export type TableView = 'details' | 'sheet1' | 'seasoned' | 'all_kg';

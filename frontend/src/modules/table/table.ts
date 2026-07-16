import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  computed,
  inject,
  signal,
  ViewChild,
} from '@angular/core';
import { SelectionModel } from '@angular/cdk/collections';
import { MatCard } from '@angular/material/card';
import { MatAnchor, MatButton } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';
import {
  MatCell,
  MatCellDef,
  MatColumnDef,
  MatHeaderCell,
  MatHeaderCellDef,
  MatHeaderRow,
  MatHeaderRowDef,
  MatRow,
  MatRowDef,
  MatTable,
} from '@angular/material/table';
import { MatCheckbox } from '@angular/material/checkbox';
import { MatPaginator } from '@angular/material/paginator';
import { MatProgressBar } from '@angular/material/progress-bar';
import { MatTab, MatTabGroup } from '@angular/material/tabs';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { FileUploadService } from '../file-upload/services/file-upload';
import { TableDataService } from './services/table-data';
import {
  DetailRow,
  PivotRow,
  ProcessedExcelResponse,
  SheetSummaryRow,
  TableColumn,
  TableView,
} from './table.models';

type CellValue = string | number | boolean | null;

interface TableRow {
  rowKey: string;
  [key: string]: CellValue;
}

@Component({
  selector: 'app-table',
  imports: [
    MatAnchor,
    MatButton,
    MatCard,
    MatIcon,
    MatTable,
    MatHeaderCell,
    MatCheckbox,
    MatCell,
    MatColumnDef,
    MatHeaderCellDef,
    MatCellDef,
    MatHeaderRow,
    MatRow,
    MatHeaderRowDef,
    MatRowDef,
    MatPaginator,
    MatProgressBar,
    MatTab,
    MatTabGroup,
  ],
  templateUrl: './table.html',
  styleUrl: './table.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Table implements OnInit, OnDestroy {
  @ViewChild(MatPaginator)
  set paginator(paginator: MatPaginator | undefined) {
    if (!paginator || paginator === this._paginator) {
      return;
    }

    this._paginatorSubscription?.unsubscribe();
    this._paginator = paginator;
    this._paginatorSubscription = paginator.page.subscribe((event) => {
      this._pageIndex.set(event.pageIndex);
      this.pageSize.set(event.pageSize);
    });
  }

  private readonly _tableDataService = inject(TableDataService);
  private readonly _fileUploadService = inject(FileUploadService);
  private readonly _router = inject(Router);
  private readonly _pageIndex = signal(0);
  private _paginator?: MatPaginator;
  private _paginatorSubscription?: Subscription;

  public readonly response = signal<ProcessedExcelResponse | null>(null);
  public readonly activeView = signal<TableView>('details');
  public readonly views: TableView[] = [
    'details',
    'sheet1',
    'seasoned',
    'all_kg',
  ];
  public readonly isLoading = signal(true);
  public readonly pageSize = signal(20);
  public readonly columnFilters = signal<Record<string, string>>({});
  public readonly selection = new SelectionModel<TableRow>(true, []);
  public readonly warnings = computed(() => this.response()?.warnings ?? []);
  public readonly visibleWarnings = computed(() => this.warnings().slice(0, 5));
  public readonly downloadUrl = computed(() => {
    const path = this.response()?.excel_file;
    return path ? this._fileUploadService.resolveApiUrl(path) : null;
  });
  public readonly outputFilename = computed(() => {
    const path = this.response()?.excel_file;
    return path?.split('/').pop() ?? 'Резултатен файл';
  });
  public readonly storedFilterCount = computed(
    () =>
      Object.values(this.columnFilters()).filter(
        (value) => value.trim().length > 0,
      ).length,
  );

  public readonly columns = computed<TableColumn<TableRow>[]>(() => {
    switch (this.activeView()) {
      case 'details':
        return [
          { key: 'date', label: 'Дата', type: 'date' },
          { key: 'documentNo', label: 'Документ' },
          { key: 'code', label: 'Код' },
          { key: 'productName', label: 'Стока' },
          { key: 'batch', label: 'Партида' },
          { key: 'quantity', label: 'Количество', type: 'number' },
          { key: 'unit', label: 'Мярка' },
          { key: 'weightKg', label: 'Тегло, кг', type: 'number' },
          { key: 'productType', label: 'Вид' },
          { key: 'stockType', label: 'Категория' },
          { key: 'isSeasonedOrGround', label: 'Овкусен/млян', type: 'boolean' },
          { key: 'partner', label: 'Партньор' },
        ];
      case 'sheet1':
        return [
          { key: 'date', label: 'Дата', type: 'date' },
          { key: 'code', label: 'Код' },
          { key: 'productName', label: 'Стока' },
          { key: 'productType', label: 'Вид' },
          { key: 'total', label: 'Общо, кг', type: 'number' },
        ];
      case 'seasoned':
      case 'all_kg':
        return [
          { key: 'batch', label: 'Партида' },
          { key: 'productType', label: 'Вид' },
          { key: 'total', label: 'Общо, кг', type: 'number' },
        ];
    }
  });

  public readonly displayedColumns = computed(() => [
    'select',
    ...this.columns().map((column) => column.key),
  ]);
  public readonly activeFilterCount = computed(() => {
    const filters = this.columnFilters();
    const activeKeys = new Set(
      this.columns().map((column) => this._sharedFilterKey(column.key)),
    );
    return [...activeKeys].filter(
      (key) => filters[key]?.trim().length > 0,
    ).length;
  });

  public readonly fullData = computed<TableRow[]>(() => {
    const response = this.response();

    if (!response) {
      return [];
    }

    switch (this.activeView()) {
      case 'details':
        return response.details.map((row, index) =>
          this._toDetailTableRow(row, index),
        );
      case 'sheet1':
        return response.sheet1.map((row, index) =>
          this._toSheetSummaryTableRow(row, index),
        );
      case 'seasoned':
        return response.pivots.seasoned.map((row, index) =>
          this._toPivotTableRow(row, index, 'seasoned'),
        );
      case 'all_kg':
        return response.pivots.all_kg.map((row, index) =>
          this._toPivotTableRow(row, index, 'all-kg'),
        );
    }
  });

  public readonly filteredData = computed(() => {
    const filters = this.columnFilters();
    const activeFilters = this.columns().filter(
      (column) =>
        filters[this._sharedFilterKey(column.key)]?.trim().length > 0,
    );

    if (activeFilters.length === 0) {
      return this.fullData();
    }

    return this.fullData().filter((row) =>
      activeFilters.every((column) =>
        this._matchesFilter(
          row[column.key],
          column,
          filters[this._sharedFilterKey(column.key)],
        ),
      ),
    );
  });

  public readonly data = computed(() => {
    const start = this._pageIndex() * this.pageSize();
    return this.filteredData().slice(start, start + this.pageSize());
  });

  public readonly selectedRowsOnPage = computed(() =>
    this.data().filter((row) => this.selection.isSelected(row)),
  );

  public readonly hasRows = computed(() => this.fullData().length > 0);
  public readonly hasFilteredRows = computed(
    () => this.filteredData().length > 0,
  );

  public ngOnInit(): void {
    const processedResponse = this._tableDataService.processedExcelResponse();

    if (processedResponse) {
      this.response.set(processedResponse);
      this.isLoading.set(false);
      return;
    }

    void this._router.navigate(['/file-upload']);
  }

  public ngOnDestroy(): void {
    this._paginatorSubscription?.unsubscribe();
  }

  public changeView(view: TableView): void {
    this.activeView.set(view);
    this._resetTableState();
  }

  public async processAnotherFile(): Promise<void> {
    this._tableDataService.clearProcessedExcelResponse();
    await this._router.navigate(['/file-upload']);
  }

  public viewAt(index: number): TableView {
    return this.views[index] ?? 'details';
  }

  public onColumnFilterChange(columnKey: string, event: Event): void {
    const value = (event.target as HTMLInputElement | HTMLSelectElement).value;
    const filters = { ...this.columnFilters() };
    const filterKey = this._sharedFilterKey(columnKey);

    if (value.trim().length > 0) {
      filters[filterKey] = value;
    } else {
      delete filters[filterKey];
    }

    this.columnFilters.set(filters);
    this._resetTableState();
  }

  public filterValue(columnKey: string): string {
    return this.columnFilters()[this._sharedFilterKey(columnKey)] ?? '';
  }

  public filterInputType(
    column: TableColumn<TableRow>,
  ): 'date' | 'search' {
    return column.type === 'date' ? 'date' : 'search';
  }

  public filterPlaceholder(column: TableColumn<TableRow>): string {
    return column.type === 'number' ? '=, >, <' : 'Филтър';
  }

  public clearColumnFilters(): void {
    this.columnFilters.set({});
    this._resetTableState();
  }

  public isPageSelected(): boolean {
    return (
      this.data().length > 0 &&
      this.selectedRowsOnPage().length === this.data().length
    );
  }

  public isPagePartiallySelected(): boolean {
    const selectedRowsOnPage = this.selectedRowsOnPage().length;
    return selectedRowsOnPage > 0 && selectedRowsOnPage < this.data().length;
  }

  public togglePageSelection(): void {
    if (this.isPageSelected()) {
      this.data().forEach((row) => this.selection.deselect(row));
      return;
    }

    this.data().forEach((row) => this.selection.select(row));
  }

  public formatCell(row: TableRow, column: TableColumn<TableRow>): string {
    const value = row[column.key];

    if (value === null || value === undefined || value === '') {
      return '-';
    }

    if (column.type === 'boolean') {
      return value ? 'Да' : 'Не';
    }

    if (column.type === 'number' && typeof value === 'number') {
      return new Intl.NumberFormat('bg-BG', {
        maximumFractionDigits: 3,
      }).format(value);
    }

    if (column.type === 'date') {
      return this._formatDate(String(value));
    }

    return String(value);
  }

  private _toDetailTableRow(row: DetailRow, index: number): TableRow {
    return {
      rowKey: `${row.document_no}-${row.code}-${row.batch}-${index}`,
      date: row.date,
      documentNo: row.document_no,
      code: row.code,
      productName: row.product_name,
      batch: row.batch,
      quantity: row.quantity,
      unit: row.unit,
      weightKg: row.weight_kg,
      productType: row.product_type,
      stockType: row.stock_type,
      isSeasonedOrGround: row.is_seasoned_or_ground,
      partner: row.partner,
    };
  }

  private _matchesFilter(
    value: CellValue,
    column: TableColumn<TableRow>,
    rawFilter: string,
  ): boolean {
    const filter = rawFilter.trim();

    if (value === null || value === undefined || value === '') {
      return false;
    }

    if (column.type === 'boolean') {
      return String(value) === filter;
    }

    if (column.type === 'date') {
      return String(value).slice(0, 10) === filter;
    }

    if (column.type === 'number') {
      return this._matchesNumberFilter(Number(value), filter);
    }

    return String(value)
      .toLocaleLowerCase('bg-BG')
      .includes(filter.toLocaleLowerCase('bg-BG'));
  }

  private _sharedFilterKey(columnKey: string): string {
    return columnKey === 'weightKg' || columnKey === 'total'
      ? 'weight'
      : columnKey;
  }

  private _matchesNumberFilter(value: number, filter: string): boolean {
    const match = filter.match(/^(<=|>=|<|>|=)?\s*(-?\d+(?:[.,]\d+)?)$/);

    if (!match) {
      return false;
    }

    const operator = match[1] ?? '=';
    const target = Number(match[2].replace(',', '.'));

    switch (operator) {
      case '<':
        return value < target;
      case '<=':
        return value <= target;
      case '>':
        return value > target;
      case '>=':
        return value >= target;
      default:
        return value === target;
    }
  }

  private _resetTableState(): void {
    this._pageIndex.set(0);
    this.selection.clear();

    if (this._paginator) {
      this._paginator.firstPage();
    }
  }

  private _toSheetSummaryTableRow(
    row: SheetSummaryRow,
    index: number,
  ): TableRow {
    return {
      rowKey: `sheet-${row['Код']}-${index}`,
      date: row['Дата'],
      code: row['Код'],
      productName: row['Стока'],
      productType: row['вид'],
      total: row.Total,
    };
  }

  private _toPivotTableRow(
    row: PivotRow,
    index: number,
    prefix: string,
  ): TableRow {
    return {
      rowKey: `${prefix}-${row['Партида']}-${row['вид']}-${index}`,
      batch: row['Партида'],
      productType: row['вид'],
      total: row.Total,
    };
  }

  private _formatDate(value: string): string {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return new Intl.DateTimeFormat('bg-BG').format(date);
  }
}

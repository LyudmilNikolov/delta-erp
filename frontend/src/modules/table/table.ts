import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  computed,
  signal,
  ViewChild,
} from '@angular/core';
import { SelectionModel } from '@angular/cdk/collections';
import { MatCard } from '@angular/material/card';
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
import { mockData } from './table.mock';
import { MatPaginator } from '@angular/material/paginator';

export interface ProductEntry {
  uuid: string;
  date: string;
  code: string;
  product: string;
  category: string;
  batch: string;
  quantity: string;
  type: string;
}

@Component({
  selector: 'app-table',
  imports: [
    MatCard,
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
  ],
  templateUrl: './table.html',
  styleUrl: './table.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Table implements AfterViewInit {
  @ViewChild(MatPaginator) paginator!: MatPaginator;

  public readonly fullData = signal<ProductEntry[]>(mockData);
  public readonly pageSize = signal(5);
  public readonly displayedColumns: string[] = [
    'select',
    'date',
    'code',
    'product',
    'category',
    'batch',
    'quantity',
    'type',
  ] as const;
  public readonly selection = new SelectionModel<ProductEntry>(true, []);

  private readonly _pageIndex = signal(0);

  public readonly data = computed(() => {
    const start = this._pageIndex() * this.pageSize();
    return this.fullData().slice(start, start + this.pageSize());
  });

  public ngAfterViewInit(): void {
    if (this.paginator) {
      this.paginator.page.subscribe((event) => {
        this._pageIndex.set(event.pageIndex);
        this.pageSize.set(event.pageSize);
      });
    }
  }
}

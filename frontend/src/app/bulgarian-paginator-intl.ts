import { Injectable } from '@angular/core';
import { MatPaginatorIntl } from '@angular/material/paginator';

@Injectable()
export class BulgarianPaginatorIntl extends MatPaginatorIntl {
  override itemsPerPageLabel = 'Редове на страница:';
  override nextPageLabel = 'Следваща страница';
  override previousPageLabel = 'Предишна страница';
  override firstPageLabel = 'Първа страница';
  override lastPageLabel = 'Последна страница';

  override getRangeLabel = (
    page: number,
    pageSize: number,
    length: number,
  ): string => {
    if (length === 0 || pageSize === 0) {
      return `0 от ${length}`;
    }

    const startIndex = page * pageSize;
    const endIndex = Math.min(startIndex + pageSize, length);
    return `${startIndex + 1}-${endIndex} от ${length}`;
  };
}

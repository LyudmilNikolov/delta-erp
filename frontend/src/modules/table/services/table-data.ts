import { Injectable, signal } from '@angular/core';
import { ProcessedExcelResponse } from '../table.models';

@Injectable({ providedIn: 'root' })
export class TableDataService {
  private readonly _processedExcelResponse =
    signal<ProcessedExcelResponse | null>(null);

  public readonly processedExcelResponse =
    this._processedExcelResponse.asReadonly();

  public setProcessedExcelResponse(response: ProcessedExcelResponse): void {
    this._processedExcelResponse.set(response);
  }

  public clearProcessedExcelResponse(): void {
    this._processedExcelResponse.set(null);
  }
}

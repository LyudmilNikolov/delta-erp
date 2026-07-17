
import { Injectable, signal } from '@angular/core';
import { ProcessedExcelResponse } from '../table.models';

@Injectable({ providedIn: 'root' })
export class TableDataService {
  private readonly _processedExcelResponse =
    signal<ProcessedExcelResponse | null>(null);
  private readonly _isMockData = signal(false);

  public readonly processedExcelResponse =
    this._processedExcelResponse.asReadonly();
  public readonly isMockData = this._isMockData.asReadonly();

  public setProcessedExcelResponse(
    response: ProcessedExcelResponse,
    isMockData = false,
  ): void {
    this._processedExcelResponse.set(response);
    this._isMockData.set(isMockData);
  }

  public clearProcessedExcelResponse(): void {
    this._processedExcelResponse.set(null);
    this._isMockData.set(false);
  }
}

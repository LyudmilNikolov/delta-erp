import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { MOCK_EXAMPLE_OUTPUT_URL } from '../table.mock';
import { ProcessedExcelResponse } from '../table.models';

@Injectable({ providedIn: 'root' })
export class TableDataService {
  private readonly _http = inject(HttpClient);
  private readonly _processedExcelResponse =
    signal<ProcessedExcelResponse | null>(null);

  public readonly processedExcelResponse =
    this._processedExcelResponse.asReadonly();

  public setProcessedExcelResponse(response: ProcessedExcelResponse): void {
    this._processedExcelResponse.set(response);
  }

  public getProcessedExcelMock(): Promise<ProcessedExcelResponse> {
    return firstValueFrom(
      this._http.get<ProcessedExcelResponse>(MOCK_EXAMPLE_OUTPUT_URL),
    );
  }
}

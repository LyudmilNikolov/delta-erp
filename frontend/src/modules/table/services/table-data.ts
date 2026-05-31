import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { MOCK_EXAMPLE_OUTPUT_URL } from '../table.mock';
import { ProcessedExcelResponse } from '../table.models';

@Injectable({ providedIn: 'root' })
export class TableDataService {
  private readonly _http = inject(HttpClient);

  public getProcessedExcelMock(): Promise<ProcessedExcelResponse> {
    return firstValueFrom(
      this._http.get<ProcessedExcelResponse>(MOCK_EXAMPLE_OUTPUT_URL),
    );
  }
}

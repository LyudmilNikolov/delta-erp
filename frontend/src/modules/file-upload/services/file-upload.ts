import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { MOCK_EXAMPLE_OUTPUT_URL } from '../../table/table.mock';
import { ProcessedExcelResponse } from '../../table/table.models';

@Injectable({ providedIn: 'root' })
export class FileUploadService {
  private readonly _apiBaseUrl = 'http://127.0.0.1:8000';
  private readonly _http = inject(HttpClient);

  public uploadFile(file: File): Promise<ProcessedExcelResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return firstValueFrom(
      this._http.post<ProcessedExcelResponse>(
        `${this._apiBaseUrl}/process`,
        formData,
      ),
    );
  }

  public loadMockData(): Promise<ProcessedExcelResponse> {
    return firstValueFrom(
      this._http.get<ProcessedExcelResponse>(MOCK_EXAMPLE_OUTPUT_URL),
    );
  }

  public resolveApiUrl(path: string): string {
    return new URL(path, `${this._apiBaseUrl}/`).toString();
  }
}

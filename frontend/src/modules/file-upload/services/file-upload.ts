import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class FileUploadService {
  // private http = inject(HttpClient)

  uploadFile(file: File): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);

    // return this.http.post('/api/upload', formData).toPromise();

    // Fake upload for demo
    return Promise.resolve('test');
  }
}

import { Component, inject, signal, computed, resource } from '@angular/core';
import { FileUploadService } from './services/file-upload';
import { MatButton } from '@angular/material/button';

@Component({
  selector: 'app-file-upload',
  templateUrl: './file-upload.html',
  styleUrls: ['./file-upload.scss'],
  imports: [MatButton],
})
export class FileUpload {
  private readonly _uploadService = inject(FileUploadService);

  public readonly file = signal<File | null>(null);

  public readonly uploadResource = resource({
    params: () => ({ file: this.file() }),
    loader: ({ params }) => this._uploadService.uploadFile(params.file!),
  });

  public onFileDrop(event: DragEvent) {
    event.preventDefault();
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.file.set(files[0]);
    }
  }

  public onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      this.file.set(input.files[0]);
    }
  }

  public onDragOver(event: DragEvent) {
    event.preventDefault();
  }

  public triggerUpload() {
    if (this.file()) {
      this.uploadResource.reload();
    }
  }
}

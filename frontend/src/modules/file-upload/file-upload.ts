import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { MatButton } from '@angular/material/button';
import { MatCard } from '@angular/material/card';
import { MatIcon } from '@angular/material/icon';
import { Router } from '@angular/router';
import { TableDataService } from '../table/services/table-data';
import { FileUploadService } from './services/file-upload';

type UploadStatus = 'ready' | 'invalid';

interface UploadFileDraft {
  file: File;
  name: string;
  extension: string;
  size: number;
  type: string;
  lastModified: number;
}

export interface UploadDraft {
  status: UploadStatus;
  files: UploadFileDraft[];
  errors: string[];
}

@Component({
  selector: 'app-file-upload',
  templateUrl: './file-upload.html',
  styleUrls: ['./file-upload.scss'],
  imports: [MatButton, MatCard, MatIcon],
})
export class FileUpload {
  private readonly _allowedExtensions = new Set(['xls', 'xlsx']);
  private readonly _fileUploadService = inject(FileUploadService);
  private readonly _router = inject(Router);
  private readonly _tableDataService = inject(TableDataService);

  public readonly draft = signal<UploadDraft | null>(null);
  public readonly isDragging = signal(false);
  public readonly isUploading = signal(false);
  public readonly uploadError = signal<string | null>(null);

  public readonly files = computed(() => this.draft()?.files ?? []);
  public readonly validationErrors = computed(() => this.draft()?.errors ?? []);
  public readonly errors = computed(() => [
    ...this.validationErrors(),
    ...(this.uploadError() ? [this.uploadError() as string] : []),
  ]);
  public readonly canSubmit = computed(
    () => this.draft()?.status === 'ready' && !this.isUploading(),
  );
  public readonly totalSize = computed(() =>
    this.files().reduce((total, file) => total + file.size, 0),
  );

  public onBrowseSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this._setFiles(input.files);
    input.value = '';
  }

  public onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(false);
    this._setFiles(event.dataTransfer?.files ?? null);
  }

  public onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(true);
  }

  public onDragLeave(event: DragEvent): void {
    if (event.currentTarget === event.target) {
      this.isDragging.set(false);
    }
  }

  public removeFile(fileToRemove: UploadFileDraft): void {
    const currentDraft = this.draft();

    if (!currentDraft) {
      return;
    }

    this._createDraft(
      currentDraft.files
        .filter((file) => file !== fileToRemove)
        .map((file) => file.file),
    );
  }

  public clear(): void {
    this.draft.set(null);
    this.isDragging.set(false);
    this.uploadError.set(null);
  }

  public async upload(): Promise<void> {
    const currentDraft = this.draft();

    if (!currentDraft || currentDraft.status !== 'ready') {
      return;
    }

    this.isUploading.set(true);
    this.uploadError.set(null);

    try {
      const response = await this._fileUploadService.uploadFile(
        currentDraft.files[0].file,
      );
      this._tableDataService.setProcessedExcelResponse(response);
      await this._router.navigate(['/table']);
    } catch (error) {
      this.uploadError.set(this._toUploadError(error));
    } finally {
      this.isUploading.set(false);
    }
  }

  public fileSize(bytes: number): string {
    if (bytes === 0) {
      return '0 B';
    }

    const units = ['B', 'KB', 'MB', 'GB'];
    const unitIndex = Math.min(
      Math.floor(Math.log(bytes) / Math.log(1024)),
      units.length - 1,
    );
    const value = bytes / 1024 ** unitIndex;

    return `${value.toFixed(value >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
  }

  private _setFiles(files: FileList | null): void {
    this._createDraft(files ? Array.from(files) : []);
  }

  private _createDraft(files: File[]): void {
    const mappedFiles = files.map((file) => this._toFileDraft(file));
    const errors = this._validateFiles(mappedFiles);

    if (mappedFiles.length === 0) {
      this.draft.set(null);
      this.uploadError.set(null);
      return;
    }

    this.draft.set({
      status: errors.length > 0 ? 'invalid' : 'ready',
      files: mappedFiles,
      errors,
    });
    this.uploadError.set(null);
  }

  private _toFileDraft(file: File): UploadFileDraft {
    const extension = file.name.split('.').pop()?.toLowerCase() ?? '';

    return {
      file,
      name: file.name,
      extension,
      size: file.size,
      type: file.type || 'application/octet-stream',
      lastModified: file.lastModified,
    };
  }

  private _validateFiles(files: UploadFileDraft[]): string[] {
    const errors: string[] = [];

    if (files.length === 0) {
      errors.push('Изберете Excel файл, за да продължите.');
    }

    if (files.length > 1) {
      errors.push('Изберете само един Excel файл.');
    }

    const invalidFiles = files.filter(
      (file) => !this._allowedExtensions.has(file.extension),
    );

    if (invalidFiles.length > 0) {
      errors.push('Поддържат се само файлове във формат .xls и .xlsx.');
    }

    return errors;
  }

  private _toUploadError(error: unknown): string {
    if (error instanceof HttpErrorResponse) {
      const backendError = error.error?.error;

      if (typeof backendError === 'string' && backendError.length > 0) {
        return backendError;
      }
    }

    return 'Файлът не може да бъде обработен. Опитайте отново.';
  }
}

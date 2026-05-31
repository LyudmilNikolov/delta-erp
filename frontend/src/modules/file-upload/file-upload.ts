import { Component, computed, signal } from '@angular/core';
import { MatButton } from '@angular/material/button';
import { MatCard } from '@angular/material/card';
import { MatIcon } from '@angular/material/icon';

type UploadSource = 'browse' | 'drop';
type UploadStatus = 'idle' | 'ready' | 'invalid';

interface UploadFileDraft {
  file: File;
  name: string;
  extension: string;
  size: number;
  type: string;
  lastModified: number;
}

export interface UploadDraft {
  source: UploadSource;
  status: UploadStatus;
  createdAt: string;
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

  public readonly draft = signal<UploadDraft | null>(null);
  public readonly isDragging = signal(false);

  public readonly files = computed(() => this.draft()?.files ?? []);
  public readonly errors = computed(() => this.draft()?.errors ?? []);
  public readonly canSubmit = computed(() => this.draft()?.status === 'ready');
  public readonly totalSize = computed(() =>
    this.files().reduce((total, file) => total + file.size, 0),
  );

  public onBrowseSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this._setFiles(input.files, 'browse');
    input.value = '';
  }

  public onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(false);
    this._setFiles(event.dataTransfer?.files ?? null, 'drop');
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
      currentDraft.source,
    );
  }

  public clear(): void {
    this.draft.set(null);
    this.isDragging.set(false);
  }

  public prepareUpload(): void {
    const currentDraft = this.draft();

    if (!currentDraft || currentDraft.status !== 'ready') {
      return;
    }

    this.draft.set({
      ...currentDraft,
      createdAt: new Date().toISOString(),
    });
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

  private _setFiles(files: FileList | null, source: UploadSource): void {
    this._createDraft(files ? Array.from(files) : [], source);
  }

  private _createDraft(files: File[], source: UploadSource): void {
    const mappedFiles = files.map((file) => this._toFileDraft(file));
    const errors = this._validateFiles(mappedFiles);

    if (mappedFiles.length === 0) {
      this.draft.set(null);
      return;
    }

    this.draft.set({
      source,
      status: errors.length > 0 ? 'invalid' : 'ready',
      createdAt: new Date().toISOString(),
      files: mappedFiles,
      errors,
    });
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
      errors.push('Select an Excel file before continuing.');
    }

    const invalidFiles = files.filter(
      (file) => !this._allowedExtensions.has(file.extension),
    );

    if (invalidFiles.length > 0) {
      errors.push('Only .xls and .xlsx files are supported.');
    }

    return errors;
  }
}

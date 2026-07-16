import { Routes } from '@angular/router';
import { FileUpload } from '../modules/file-upload/file-upload';
import { Table } from '../modules/table/table';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'file-upload',
  },
  {
    path: 'dashboard',
    redirectTo: 'file-upload',
  },
  {
    path: 'table',
    component: Table,
  },
  {
    path: 'file-upload',
    component: FileUpload,
  },
  {
    path: '**',
    redirectTo: 'file-upload',
  },
];

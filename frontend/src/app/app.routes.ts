import { Routes } from '@angular/router';
import { Dashboard } from '../modules/dashboard/dashboard';
import { FileUpload } from '../modules/file-upload/file-upload';
import { Table } from '../modules/table/table';

export const routes: Routes = [
  {
    path: 'dashboard',
    component: Dashboard,
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
    redirectTo: 'dashboard',
  },
];

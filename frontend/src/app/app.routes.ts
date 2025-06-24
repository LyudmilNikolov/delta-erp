import { Routes } from '@angular/router';
import { Dashboard } from '../modules/dashboard/dashboard';
import { FileUpload } from '../modules/file-upload/file-upload';

export const routes: Routes = [
  {
    path: 'dashboard',
    component: Dashboard,
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

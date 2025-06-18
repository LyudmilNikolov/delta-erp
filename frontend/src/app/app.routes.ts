import { Routes } from '@angular/router';
import {Dashboard} from '../modules/dashboard/dashboard';

export const routes: Routes = [
  {
    path: '',
    component: Dashboard,
  },
  {
    path: '**',
    redirectTo: 'dashboard'
  },
];

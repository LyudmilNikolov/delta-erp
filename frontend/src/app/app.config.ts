import {
  ApplicationConfig,
  provideBrowserGlobalErrorListeners,
  provideZonelessChangeDetection,
} from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { MatPaginatorIntl } from '@angular/material/paginator';
import { provideRouter } from '@angular/router';

import { BulgarianPaginatorIntl } from './bulgarian-paginator-intl';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    provideHttpClient(),
    provideRouter(routes),
    { provide: MatPaginatorIntl, useClass: BulgarianPaginatorIntl },
  ],
};

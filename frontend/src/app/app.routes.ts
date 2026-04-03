import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';
import { roleGuard } from './guards/role.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./components/login/login.component').then(m => m.LoginComponent)
  },

  {
    path: 'hr',
    canActivate: [authGuard, roleGuard],
    data: { role: 'hr' },   // ✅ only HR
    loadComponent: () =>
      import('./components/hr/hr.component').then(m => m.HrComponent)
  },

  {
    path: 'user',
    canActivate: [authGuard, roleGuard],
    data: { role: 'user' }, // ✅ only USER
    loadComponent: () =>
      import('./components/user/user.component').then(m => m.UserComponent)
  }
];
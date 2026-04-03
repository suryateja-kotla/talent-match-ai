import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);

  const user =
    localStorage.getItem('currentUser') ||
    sessionStorage.getItem('currentUser');

  if (user) {
    return true;
  } else {
    router.navigate(['/']);
    return false;
  }
};
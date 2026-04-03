import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';

export const roleGuard: CanActivateFn = (route) => {
  const router = inject(Router);

  // get user from storage
  const userData =
    localStorage.getItem('currentUser') ||
    sessionStorage.getItem('currentUser');

  if (!userData) {
    router.navigate(['/']);
    return false;
  }

  const user = JSON.parse(userData);

  const expectedRole = route.data?.['role'];

  if (user.role === expectedRole) {
    return true;  // ✅ allowed
  }

  // ❌ wrong role → redirect
  if (user.role === 'hr') {
    router.navigate(['/hr']);
  } else {
    router.navigate(['/user']);
  }

  return false;
};
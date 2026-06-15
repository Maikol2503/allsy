import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../../features/auth/services/services.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isLoggedIn()) {
    return true; // ✅ Usuario autenticado, permitir acceso
  } else {
    // ❌ No autenticado, redirigir al login
    router.navigate(['/login']);
    return false;
  }
};

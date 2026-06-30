import { Injectable, Injector } from '@angular/core'; // 👈 1. Importante: Añadir Injector aquí
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, switchMap, filter, take } from 'rxjs/operators';
import { AuthService } from '../../features/auth/services/services.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private isRefreshing = false;
  private refreshTokenSubject: BehaviorSubject<any> = new BehaviorSubject<any>(null);

  // 👈 2. Inyectamos solo el Injector para evitar el bucle circular
  constructor(private injector: Injector) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // 👈 3. Obtenemos el servicio manualmente usando el injector
    const authService = this.injector.get(AuthService);
    const token = authService.getToken(); // Usamos el método que ya tienes en el service
    
    console.log(`🚀 [Interceptor] Petición saliente a: ${req.url}`);

    let request = req;
    if (token) {
      request = this.addTokenHeader(req, token);
    }

    return next.handle(request).pipe(
      catchError((error) => {
        if (error instanceof HttpErrorResponse && error.status === 401) {
          // Evitar bucle infinito si la petición que falló fue precisamente el refresh
          if (request.url.includes('/refresh')) {
            return throwError(() => error);
          }
          console.warn('⚠️ [Interceptor] ¡Token expirado (401)! Iniciando recuperación...');
          return this.handle401Error(request, next);
        }
        return throwError(() => error);
      })
    );
  }

  private handle401Error(request: HttpRequest<any>, next: HttpHandler) {
    const authService = this.injector.get(AuthService);

    if (!this.isRefreshing) {
      this.isRefreshing = true;
      this.refreshTokenSubject.next(null);
      console.log('🔄 [Interceptor] Solicitando nuevo Access Token al servidor...');

      const refreshToken = localStorage.getItem('refresh_token');

      return authService.refreshToken(refreshToken).pipe(
        switchMap((res: any) => {
          console.log('✅ [Interceptor] ¡Token renovado con éxito!');
          this.isRefreshing = false;
          
          localStorage.setItem('access_token', res.access_token);
          this.refreshTokenSubject.next(res.access_token);
          
          console.log('🔁 [Interceptor] Re-intentando petición original con el nuevo token.');
          return next.handle(this.addTokenHeader(request, res.access_token));
        }),
        catchError((err) => {
          console.error('❌ [Interceptor] El Refresh Token también falló. Cerrando sesión.');
          this.isRefreshing = false;
          authService.logout();
          return throwError(() => err);
        })
      );
    }

    console.log('⏳ [Interceptor] Ya hay un refresh en curso. Encolando esta petición...');
    return this.refreshTokenSubject.pipe(
      filter(token => token !== null),
      take(1),
      switchMap((token) => {
        console.log('📤 [Interceptor] Liberando petición encolada con el nuevo token.');
        return next.handle(this.addTokenHeader(request, token));
      })
    );
  }

  private addTokenHeader(request: HttpRequest<any>, token: string) {
    return request.clone({
      setHeaders: { Authorization: `Bearer ${token}` }
    });
  }
}
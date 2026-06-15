import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { Router } from '@angular/router'; // ✨ Importamos Router para el logout

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  nombre: string;
  email: string;
  password: string;
}

// ✨ Actualizamos la interfaz para incluir el refresh_token
interface TokenResponse {
  access_token: string;
  refresh_token: string; // 👈 Este viene de tu Backend ahora
  token_type: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private apiUrl = 'http://localhost:8000/api/v1/auth';

  constructor(private http: HttpClient, private router: Router) {}

  // ✅ Registro de usuario
  register(data: RegisterRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/register`, data);
  }

  // ✅ Inicio de sesión (Actualizado para guardar ambos tokens)
  login(data: LoginRequest): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.apiUrl}/login`, data).pipe(
      tap((response) => {
        // 💾 Guardamos AMBOS tokens
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);
      })
    );
  }

  // ✅ REFRESH TOKEN (La función que el Interceptor necesita ✨)
  refreshToken(token: string | null): Observable<any> {
  console.log('📡 [AuthService] Enviando POST a /refresh...');
  const formData = new FormData();
  formData.append('refresh_token', token || '');

  return this.http.post<any>(`${this.apiUrl}/refresh`, formData);
}

  // ✅ Cerrar sesión (Actualizado para limpiar todo)
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.router.navigate(['/login']); // Redirigimos al usuario
  }

  // ✅ Obtener token de acceso
  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  // ✅ Obtener token de refresco
  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  // ✅ Saber si el usuario está logueado
  isLoggedIn(): boolean {
    return !!this.getToken();
  }
}

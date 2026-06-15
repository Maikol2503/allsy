import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from '../services/services.service';


@Component({
  selector: 'app-login',
  standalone: true, // 👈 importante
  imports: [FormsModule, CommonModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  email: string = '';
  password: string = '';
  errorMessage: string = '';
  loading: boolean = false;

  constructor(private authService: AuthService, private router: Router) {}

  onLogin() {
    this.loading = true;
    this.errorMessage = '';

    this.authService.login({ email: this.email, password: this.password }).subscribe({
      next: (res) => {
        console.log('✅ Login exitoso:', res);
        this.loading = false;
        this.router.navigate(['/']); // 🔹 Redirige al dashboard
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error.detail || 'Error al iniciar sesión';
      },
    });
  }
}


import { Component } from '@angular/core';
import { AuthService } from '../../../features/auth/services/services.service';
import { Router, RouterModule } from '@angular/router';

@Component({
  selector: 'app-navbar',
  imports: [RouterModule],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css'
})
export class NavbarComponent {
constructor(private authService: AuthService, private router: Router) {}

  logout() {
    this.authService.logout(); // 🔹 Elimina el token del localStorage
    this.router.navigate(['/login']); // 🔹 Redirige al login
  }
}

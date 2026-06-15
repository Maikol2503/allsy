import { Component } from '@angular/core';
import { AuthService } from '../../../features/auth/services/services.service';
import { Router, RouterLink, RouterModule } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink, RouterModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.css'
})
export class SidebarComponent {
constructor(private authService: AuthService, private router: Router) {}

  logout() {
    this.authService.logout(); // 🔹 Elimina el token del localStorage
    this.router.navigate(['/login']); // 🔹 Redirige al login
  }
}

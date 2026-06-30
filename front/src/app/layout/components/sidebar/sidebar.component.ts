import { Component } from '@angular/core';
import { AuthService } from '../../../features/auth/services/services.service';
import { Router, RouterLink, RouterModule, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink, RouterModule, RouterLinkActive, CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.css'
})
export class SidebarComponent {
  openMenu: string | null = null;

  constructor(private authService: AuthService, private router: Router) {}

  toggleMenu(menuName: string) {
    this.openMenu = this.openMenu === menuName ? null : menuName;
  }

  logout() {
    this.authService.logout(); // 🔹 Elimina el token del localStorage
    this.router.navigate(['/login']); // 🔹 Redirige al login
  }
}

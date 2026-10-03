import { Component, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ETIQUETAS_ROL } from '../../services/permisos';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.scss',
})
export class SidebarComponent {
  // Rol activo legible para mostrarlo bajo el correo
  public etiquetaRol = computed(() => {
    const rol = this.authService.rolActivo();
    return rol ? ETIQUETAS_ROL[rol] : '';
  });

  constructor(public authService: AuthService) {}
}

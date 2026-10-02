import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html'
})
export class Login {
  private authService = inject(AuthService);
  public readonly adminEmail = 'admin@admin.org';

  public email = '';
  public password = '';
  public selectedRole = 'empleado';
  public availableRoles: string[] = ['empleado']; // Todos tienen empleado por defecto
  
  public step: 1 | 2 = 1; // 1: Pedir email, 2: Pedir contraseña y rol
  public errorMessage = '';
  public isLoading = false;

  public isAdminEmail() {
    return this.email.trim().toLowerCase() === this.adminEmail;
  }

  // Paso 1: Verificar el email y cargar los roles desde Flask
  public onCheckEmail() {
    if (!this.email) {
      this.errorMessage = 'Por favor, introduce tu correo electrónico.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.authService.obtenerRolesPorEmail(this.email).subscribe({
      next: (response: any) => {
        this.isLoading = false;
        // response.roles contendrá un array como ['empleado', 'hr', 'vi']
        this.availableRoles = response.roles && response.roles.length > 0 ? response.roles : ['empleado'];
        this.selectedRole = 'empleado'; // Por defecto se selecciona empleado

        if (this.isAdminEmail() || this.availableRoles.length === 1) {
          this.onLogin();
        } else {
          this.step = 2; // Elegimos el rol antes de validar el login
        }
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.message || 'Correo no encontrado en la base de datos.';
      }
    });
  }

  // Paso 2: Enviar credenciales completas con el rol elegido
  public onLogin() {
    if (!this.isAdminEmail() && !this.password) {
      this.errorMessage = 'Por favor, introduce tu contraseña.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.authService.login(this.email, this.password, this.selectedRole).subscribe({
      next: () => {
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.message || 'Contraseña incorrecta.';
      }
    });
  }

  public volverAEmail() {
    this.step = 1;
    this.password = '';
    this.errorMessage = '';
  }
}
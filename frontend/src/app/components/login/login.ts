import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import { ETIQUETAS_ROL, Rol } from '../../services/permisos';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html'
})
export class Login {
  private authService = inject(AuthService);
  // La app no usa zone.js: tras cada respuesta HTTP hay que pedir que se repinte
  private readonly changeDetector = inject(ChangeDetectorRef);
  public readonly etiquetasRol = ETIQUETAS_ROL;

  public email = '';
  public password = '';
  public selectedRole: Rol = 'empleado';
  public availableRoles: Rol[] = ['empleado']; // Todos tienen empleado por defecto
  
  public step: 1 | 2 = 1; // 1: Pedir correo y contraseña, 2: Elegir perfil
  public errorMessage = '';
  public isLoading = false;

  // Paso 1: Validar correo y contraseña y cargar los perfiles del usuario
  public onCheckCredentials() {
    if (!this.email || !this.password) {
      this.errorMessage = 'Introduce tu correo electrónico y tu contraseña.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.authService.obtenerRoles(this.email, this.password).subscribe({
      next: (response) => {
        this.isLoading = false;
        // El servidor devuelve los roles ordenados por prioridad: ['hr', 'mando', 'empleado']
        this.availableRoles = response.roles?.length ? response.roles : ['empleado'];
        this.selectedRole = this.availableRoles[0]; // Se preselecciona el de mayor prioridad

        if (this.availableRoles.length === 1) {
          this.onLogin();
        } else {
          this.step = 2; // Credenciales correctas: falta elegir el perfil
        }
        this.changeDetector.markForCheck();
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.message || 'Correo o contraseña incorrectos.';
        this.changeDetector.markForCheck();
      }
    });
  }

  // Paso 2 (o directo si solo hay un perfil): obtener el token con el rol elegido
  public onLogin() {
    if (!this.password) {
      this.errorMessage = 'Por favor, introduce tu contraseña.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.authService.login(this.email, this.password, this.selectedRole).subscribe({
      next: () => {
        this.isLoading = false;
        this.changeDetector.markForCheck();
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.message || 'Contraseña incorrecta.';
        this.changeDetector.markForCheck();
      }
    });
  }

  public volverAEmail() {
    this.step = 1;
    this.password = '';
    this.errorMessage = '';
  }
}
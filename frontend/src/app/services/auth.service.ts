import { Injectable, signal, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  public isLogged = signal<boolean>(false);
  public usuarioActual = signal<any>(null);
  public rolActivo = signal<string>('empleado');

  private apiUrl = 'http://localhost:5000/api';

  // 1. Consulta los roles disponibles para un email antes del password
  public obtenerRolesPorEmail(email: string) {
    return this.http.post<any>(`${this.apiUrl}/get-roles`, { email });
  }

  // 2. Realiza el login enviando correo, contraseña y el rol elegido
  public login(email: string, password: string, rol: string) {
    return this.http.post(`${this.apiUrl}/login`, { email, password, rol }).pipe(
      tap((response: any) => {
        this.isLogged.set(true);
        this.usuarioActual.set(response.user);
        this.rolActivo.set(rol);
        this.router.navigate(['/resumen-general']);
      })
    );
  }

  public logout() {
    this.isLogged.set(false);
    this.usuarioActual.set(null);
    this.rolActivo.set('empleado');
    this.router.navigate(['/login']);
  }
}
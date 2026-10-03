import { Injectable, computed, signal, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs';
import { Rol, puedeVerRuta, rutaInicio } from './permisos';

export interface UsuarioSesion {
  email: string;
  pernr: string;
  nombre?: string;
  rolActivo: Rol;
}

interface RespuestaLogin {
  success: boolean;
  token: string;
  user: UsuarioSesion & { roles: Rol[] };
}

export const API_URL = 'http://localhost:5000/api';
const CLAVE_TOKEN = 'tirme_token';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  private tokenActual = signal<string | null>(null);
  public usuarioActual = signal<UsuarioSesion | null>(null);
  public isLogged = computed(() => this.usuarioActual() !== null);
  public rolActivo = computed<Rol | null>(() => this.usuarioActual()?.rolActivo ?? null);

  constructor() {
    // Mantener la sesión al recargar: se recupera el token guardado si sigue vigente
    this.restaurarSesion();
  }

  public token(): string | null {
    return this.tokenActual();
  }

  // 1. Valida correo y contraseña y devuelve los perfiles disponibles del usuario
  public obtenerRoles(email: string, password: string) {
    return this.http.post<{ success: boolean; roles: Rol[] }>(`${API_URL}/get-roles`, { email, password });
  }

  // 2. Realiza el login enviando correo, contraseña y el rol elegido
  public login(email: string, password: string, rol: Rol) {
    return this.http.post<RespuestaLogin>(`${API_URL}/login`, { email, password, rol }).pipe(
      tap((response) => {
        this.guardarToken(response.token);
        this.usuarioActual.set({
          email: response.user.email,
          pernr: response.user.pernr,
          nombre: response.user.nombre,
          rolActivo: response.user.rolActivo,
        });
        this.router.navigateByUrl(rutaInicio(response.user.rolActivo));
      })
    );
  }

  public logout() {
    this.borrarToken();
    this.usuarioActual.set(null);
    this.router.navigate(['/login']);
  }

  public puedeVer(ruta: string): boolean {
    return puedeVerRuta(this.rolActivo(), ruta);
  }

  public rutaInicio(): string {
    return rutaInicio(this.rolActivo());
  }

  private restaurarSesion() {
    const token = this.leerAlmacenamiento();
    const payload = token ? decodificarPayload(token) : null;
    if (!token || !payload || payload.exp * 1000 <= Date.now()) {
      this.borrarToken();
      return;
    }
    this.tokenActual.set(token);
    this.usuarioActual.set({
      email: payload.email,
      pernr: payload.sub,
      rolActivo: payload.rol_activo,
    });
  }

  private guardarToken(token: string) {
    this.tokenActual.set(token);
    try {
      localStorage.setItem(CLAVE_TOKEN, token);
    } catch {
      // Sin almacenamiento disponible la sesión dura hasta recargar
    }
  }

  private borrarToken() {
    this.tokenActual.set(null);
    try {
      localStorage.removeItem(CLAVE_TOKEN);
    } catch {
      // Nada que borrar
    }
  }

  private leerAlmacenamiento(): string | null {
    try {
      return localStorage.getItem(CLAVE_TOKEN);
    } catch {
      return null;
    }
  }
}

interface PayloadJwt {
  sub: string;
  exp: number;
  email: string;
  rol_activo: Rol;
}

/** Lee el payload de un JWT (sin verificar la firma: eso lo hace el backend). */
export function decodificarPayload(token: string): PayloadJwt | null {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const json = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + c.charCodeAt(0).toString(16).padStart(2, '0'))
        .join('')
    );
    const payload = JSON.parse(json);
    return payload?.sub && payload?.exp && payload?.rol_activo ? payload : null;
  } catch {
    return null;
  }
}

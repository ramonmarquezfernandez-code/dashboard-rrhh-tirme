import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { authInterceptor } from './auth.interceptor';
import { API_URL, AuthService } from '../services/auth.service';

function tokenVigente(): string {
  const payload = btoa(JSON.stringify({
    sub: '00000001', email: 'jperez@empresa.local', rol_activo: 'empleado',
    exp: Math.floor(Date.now() / 1000) + 3600,
  })).replace(/=+$/, '');
  return `cabecera.${payload}.firma`;
}

describe('authInterceptor', () => {
  let http: HttpClient;
  let backend: HttpTestingController;
  let authService: AuthService;

  beforeEach(() => {
    localStorage.setItem('tirme_token', tokenVigente());
    TestBed.configureTestingModule({
      providers: [
        provideRouter([{ path: 'login', children: [] }]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpClient);
    backend = TestBed.inject(HttpTestingController);
    authService = TestBed.inject(AuthService);
  });

  afterEach(() => {
    backend.verify();
    localStorage.clear();
  });

  it('añade el token a las peticiones a la API', () => {
    http.get(`${API_URL}/partes/estados`).subscribe();
    const peticion = backend.expectOne(`${API_URL}/partes/estados`);
    expect(peticion.request.headers.get('Authorization')).toBe(`Bearer ${authService.token()}`);
    peticion.flush([]);
  });

  it('no envía el token al login ni a servidores externos', () => {
    http.post(`${API_URL}/login`, {}).subscribe();
    http.get('https://ejemplo.com/datos').subscribe();
    const login = backend.expectOne(`${API_URL}/login`);
    const externa = backend.expectOne('https://ejemplo.com/datos');
    expect(login.request.headers.has('Authorization')).toBe(false);
    expect(externa.request.headers.has('Authorization')).toBe(false);
    login.flush({});
    externa.flush({});
  });

  it('cierra la sesión si la API responde 401', () => {
    expect(authService.isLogged()).toBe(true);
    http.get(`${API_URL}/partes`).subscribe({ error: () => {} });
    backend
      .expectOne(`${API_URL}/partes`)
      .flush({ message: 'caducada' }, { status: 401, statusText: 'Unauthorized' });
    expect(authService.isLogged()).toBe(false);
  });
});

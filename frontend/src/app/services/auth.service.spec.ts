import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { AuthService, decodificarPayload } from './auth.service';

// Crea un JWT sin firma válida (el frontend solo lee el payload)
function tokenFalso(payload: object): string {
  const base64url = (obj: object) =>
    btoa(JSON.stringify(obj)).replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_');
  return `${base64url({ alg: 'HS256', typ: 'JWT' })}.${base64url(payload)}.firma`;
}

const ahoraEnSegundos = () => Math.floor(Date.now() / 1000);

function crearServicio(): AuthService {
  TestBed.configureTestingModule({ providers: [provideRouter([{ path: 'login', children: [] }]), provideHttpClient()] });
  return TestBed.inject(AuthService);
}

describe('AuthService', () => {
  beforeEach(() => localStorage.clear());

  it('restaura la sesión al recargar si el token guardado sigue vigente', () => {
    localStorage.setItem('tirme_token', tokenFalso({
      sub: '00000002', email: 'mgarcia@empresa.local', rol_activo: 'mando', exp: ahoraEnSegundos() + 3600,
    }));
    const servicio = crearServicio();
    expect(servicio.isLogged()).toBe(true);
    expect(servicio.rolActivo()).toBe('mando');
    expect(servicio.usuarioActual()?.pernr).toBe('00000002');
    expect(servicio.token()).not.toBeNull();
  });

  it('descarta un token caducado', () => {
    localStorage.setItem('tirme_token', tokenFalso({
      sub: '00000001', email: 'jperez@empresa.local', rol_activo: 'empleado', exp: ahoraEnSegundos() - 10,
    }));
    const servicio = crearServicio();
    expect(servicio.isLogged()).toBe(false);
    expect(localStorage.getItem('tirme_token')).toBeNull();
  });

  it('descarta un token corrupto', () => {
    localStorage.setItem('tirme_token', 'esto-no-es-un-jwt');
    expect(crearServicio().isLogged()).toBe(false);
  });

  it('logout borra el token y la sesión', () => {
    localStorage.setItem('tirme_token', tokenFalso({
      sub: '00000004', email: 'atorres@empresa.local', rol_activo: 'hr', exp: ahoraEnSegundos() + 3600,
    }));
    const servicio = crearServicio();
    servicio.logout();
    expect(servicio.isLogged()).toBe(false);
    expect(servicio.token()).toBeNull();
    expect(localStorage.getItem('tirme_token')).toBeNull();
  });

  it('decodifica payloads con caracteres no ASCII', () => {
    const json = JSON.stringify({ sub: '1', exp: 1, rol_activo: 'hr', email: 'maría@empresa.local' });
    const payload = btoa(String.fromCharCode(...new TextEncoder().encode(json))).replace(/=+$/, '');
    expect(decodificarPayload(`x.${payload}.y`)?.email).toBe('maría@empresa.local');
  });
});

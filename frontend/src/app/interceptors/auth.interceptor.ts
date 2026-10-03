import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { API_URL, AuthService } from '../services/auth.service';

// Añade el JWT a las peticiones a la API y cierra la sesión si el backend
// responde 401 (token caducado o no válido).
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.token();
  const esApi = req.url.startsWith(API_URL);
  const esLogin = req.url === `${API_URL}/login` || req.url === `${API_URL}/get-roles`;

  const peticion = esApi && token && !esLogin
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(peticion).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && esApi && !esLogin && authService.isLogged()) {
        authService.logout();
      }
      return throwError(() => error);
    })
  );
};

import { inject, Type } from '@angular/core';
import { ActivatedRouteSnapshot, Route, Router, Routes } from '@angular/router';
import { AuthService } from './services/auth.service';
import { Login } from './components/login/login';
import { ResumenGeneral } from './components/resumen-general/resumen-general';
import { Personas } from './components/personas/personas';
import { HorasExtra } from './components/horas-extra/horas-extra';
import { HorasExtraEmpleados } from './components/horas-extra-empleados/horas-extra-empleados';
import { RankingCombo } from './components/ranking-combo/ranking-combo';
import { SpRetribuidas } from './components/sp-retribuidas/sp-retribuidas';
import { ParteFormulario } from './components/parte-formulario/parte-formulario';
import { MisPartes } from './components/mis-partes/mis-partes';

// Exige sesión y que el rol activo pueda ver la ruta (ver services/permisos.ts)
const authGuard = (route: ActivatedRouteSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  if (!authService.isLogged()) {
    return router.createUrlTree(['/login']);
  }
  const ruta = route.routeConfig?.path ?? '';
  return authService.puedeVer(ruta) || router.createUrlTree([authService.rutaInicio()]);
};

const loginGuard = () => {
  const authService = inject(AuthService);
  return !authService.isLogged() || inject(Router).createUrlTree([authService.rutaInicio()]);
};

// Pantalla protegida: el título se muestra en la cabecera (data.titulo) y en la pestaña (title)
function pantalla(path: string, component: Type<unknown>, titulo: string): Route[] {
  return [{ path, component, canActivate: [authGuard], title: `${titulo} · Tirme RRHH`, data: { titulo } }];
}

// '' y rutas desconocidas: al login, que redirige a la pantalla de inicio si ya hay sesión
export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: Login, canActivate: [loginGuard] },
  ...pantalla('nuevo-parte', ParteFormulario, 'Nuevo parte de trabajo'),
  ...pantalla('mis-partes', MisPartes, 'Mis partes de trabajo'),
  ...pantalla('mis-partes/:mandt', ParteFormulario, 'Parte de trabajo'),
  ...pantalla('resumen-general', ResumenGeneral, 'Resumen general de plantilla'),
  ...pantalla('personal', Personas, 'Directorio de personal'),
  ...pantalla('horas-extra', HorasExtra, 'Horas extra por periodos'),
  ...pantalla('horas-extra-empleados', HorasExtraEmpleados, 'Horas extra por empleado'),
  ...pantalla('ranking-combo', RankingCombo, 'Ranking HE combo'),
  ...pantalla('sp-retribuidas', SpRetribuidas, 'Total SP retribuidas'),
  { path: '**', redirectTo: 'login' }
];

import { inject } from '@angular/core';
import { Router, Routes } from '@angular/router';
import { AuthService } from './services/auth.service';
import { Login } from './components/login/login';
import { ResumenGeneral } from './components/resumen-general/resumen-general';
import { Personas } from './components/personas/personas';
import { Turnos } from './components/turnos/turnos';
import { HorasExtra } from './components/horas-extra/horas-extra';
import { HorasExtraEmpleados } from './components/horas-extra-empleados/horas-extra-empleados';
import { RankingCombo } from './components/ranking-combo/ranking-combo';
import { SpRetribuidas } from './components/sp-retribuidas/sp-retribuidas';

const authGuard = () => {
  const authService = inject(AuthService);
  return authService.isLogged() || inject(Router).createUrlTree(['/login']);
};

const loginGuard = () => {
  const authService = inject(AuthService);
  return !authService.isLogged() || inject(Router).createUrlTree(['/resumen-general']);
};

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: Login, canActivate: [loginGuard] },
  { path: 'resumen-general', component: ResumenGeneral, canActivate: [authGuard] },
  { path: 'personal', component: Personas, canActivate: [authGuard] },
  { path: 'turnos', component: Turnos, canActivate: [authGuard] },
  { path: 'horas-extra', component: HorasExtra, canActivate: [authGuard] },
  { path: 'horas-extra-empleados', component: HorasExtraEmpleados, canActivate: [authGuard] },
  { path: 'ranking-combo', component: RankingCombo, canActivate: [authGuard] },
  { path: 'sp-retribuidas', component: SpRetribuidas, canActivate: [authGuard] },
  { path: '**', redirectTo: 'login' }
];

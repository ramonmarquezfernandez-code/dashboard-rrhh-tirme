import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { HeaderFiltros } from './header-filtros';

@Component({ template: '' })
class PantallaVacia {}

describe('HeaderFiltros', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HeaderFiltros],
      providers: [
        provideRouter([
          { path: 'horas-extra', component: PantallaVacia, data: { titulo: 'Horas extra por periodos' } },
          { path: 'personal', component: PantallaVacia, data: { titulo: 'Directorio de personal' } },
        ]),
      ],
    }).compileComponents();
  });

  it('muestra el título de la pantalla activa y lo actualiza al navegar', async () => {
    const fixture = TestBed.createComponent(HeaderFiltros);
    const router = TestBed.inject(Router);
    const titulo = () => (fixture.nativeElement as HTMLElement).querySelector('h2')?.textContent?.trim();

    await router.navigateByUrl('/horas-extra');
    await fixture.whenStable();
    expect(titulo()).toBe('Horas extra por periodos');

    await router.navigateByUrl('/personal');
    await fixture.whenStable();
    expect(titulo()).toBe('Directorio de personal');
  });
});

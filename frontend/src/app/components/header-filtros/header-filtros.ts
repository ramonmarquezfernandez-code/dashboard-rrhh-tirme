import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRouteSnapshot, NavigationEnd, Router } from '@angular/router';
import { filter } from 'rxjs';

// Cabecera de la zona de contenido: muestra el título de la pantalla actual
// (data.titulo de la ruta, ver app.routes.ts). Los filtros viven en cada pantalla.
@Component({
  selector: 'app-header-filtros',
  standalone: true,
  templateUrl: './header-filtros.html',
  styleUrl: './header-filtros.scss',
})
export class HeaderFiltros {
  private readonly router = inject(Router);
  public titulo = signal('');

  constructor() {
    this.actualizarTitulo();
    this.router.events
      .pipe(filter((evento) => evento instanceof NavigationEnd), takeUntilDestroyed(inject(DestroyRef)))
      .subscribe(() => this.actualizarTitulo());
  }

  private actualizarTitulo() {
    let ruta: ActivatedRouteSnapshot | null = this.router.routerState.snapshot.root;
    let titulo = '';
    while (ruta) {
      titulo = ruta.data['titulo'] ?? titulo;
      ruta = ruta.firstChild;
    }
    this.titulo.set(titulo);
  }
}

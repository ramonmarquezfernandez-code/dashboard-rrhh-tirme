import { Component, ChangeDetectorRef, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize, Subject, Subscription, takeUntil } from 'rxjs';
import { HeService, PlantillaGrupoResumen } from '../../services/he.service';

@Component({
  selector: 'app-resumen-general',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './resumen-general.html',
})
export class ResumenGeneral implements OnInit, OnDestroy {
  private readonly heService = inject(HeService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();
  private solicitud?: Subscription;

  // Filtros de la pantalla ('' = todos) y sus opciones, que devuelve la API según el perfil
  public grupo = signal('');
  public area = signal('');
  public grupos = signal<string[]>([]);
  public areas = signal<string[]>([]);

  // Total real de empleados activos (ACTIVE = 1) en userpayroll
  public totalPlantilla = signal(0);

  // Resúmenes de empleados activos agrupados por grupo, área y departamento
  public porGrupo = signal<PlantillaGrupoResumen[]>([]);
  public porArea = signal<PlantillaGrupoResumen[]>([]);
  public porDepartamento = signal<PlantillaGrupoResumen[]>([]);

  public isLoading = signal(false);
  public errorMessage = signal('');

  public ngOnInit() {
    this.cargar();
  }

  public cargar() {
    this.solicitud?.unsubscribe();
    this.isLoading.set(true);
    this.errorMessage.set('');

    this.solicitud = this.heService
      .obtenerPlantillaResumen({ grupo: this.grupo(), direccion: this.area() })
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.isLoading.set(false);
          this.changeDetector.markForCheck();
        }),
      )
      .subscribe({
        next: (response) => {
          this.totalPlantilla.set(response.total_plantilla || 0);
          this.porGrupo.set(response.por_grupo || []);
          this.porArea.set(response.por_area || []);
          this.porDepartamento.set(response.por_departamento || []);
          this.grupos.set(response.grupos || []);
          this.areas.set(response.areas || []);
          this.changeDetector.markForCheck();
        },
        error: (error) => {
          this.totalPlantilla.set(0);
          this.porGrupo.set([]);
          this.porArea.set([]);
          this.porDepartamento.set([]);
          this.errorMessage.set(
            error?.error?.message || 'No se ha podido cargar el resumen de plantilla.',
          );
          this.changeDetector.markForCheck();
        },
      });
  }

  public ngOnDestroy() {
    this.solicitud?.unsubscribe();
    this.destroy$.next();
    this.destroy$.complete();
  }
}

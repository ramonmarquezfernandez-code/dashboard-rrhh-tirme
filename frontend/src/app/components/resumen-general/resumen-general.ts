import { Component, ChangeDetectorRef, OnDestroy, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize, Subject, Subscription, takeUntil } from 'rxjs';
import { FiltrosService } from '../../services/filtros';
import { HeService, PlantillaGrupoResumen } from '../../services/he.service';

@Component({
  selector: 'app-resumen-general',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './resumen-general.html',
})
export class ResumenGeneral implements OnDestroy {
  public filtrosService = inject(FiltrosService);
  private readonly heService = inject(HeService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();
  private solicitud?: Subscription;

  // Total real de empleados activos (ACTIVE = 1) en userpayroll
  public totalPlantilla = signal(0);

  // Resúmenes de empleados activos agrupados por grupo, área y departamento
  public porGrupo = signal<PlantillaGrupoResumen[]>([]);
  public porArea = signal<PlantillaGrupoResumen[]>([]);
  public porDepartamento = signal<PlantillaGrupoResumen[]>([]);

  public isLoading = signal(false);
  public errorMessage = signal('');

  constructor() {
    // Recarga el resumen cada vez que cambian los filtros globales
    effect(() => {
      const filtros = this.filtrosService.filtros();
      this.cargar(filtros.grupo, filtros.direccion);
    });
  }

  private cargar(grupo: string, direccion: string) {
    this.solicitud?.unsubscribe();
    this.isLoading.set(true);
    this.errorMessage.set('');

    this.solicitud = this.heService
      .obtenerPlantillaResumen({ grupo, direccion })
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


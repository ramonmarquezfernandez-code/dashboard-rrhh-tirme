import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, inject, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize, Subject, Subscription, takeUntil } from 'rxjs';
import { HeEmpleado, HePeriodo, HeService } from '../../services/he.service';

@Component({
  selector: 'app-horas-extra-empleados',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './horas-extra-empleados.html',
  styleUrl: './horas-extra-empleados.scss',
})
export class HorasExtraEmpleados implements OnInit, OnDestroy {
  private readonly heService = inject(HeService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();
  private solicitud?: Subscription;

  public anio = 2026;
  public mesDesde = 1;
  public mesHasta = 12;
  public anioNatural = false;
  public departamento = '';
  public trabajador = '';
  public estado = '';
  public periodo = '';
  public orden = 'horas';

  public readonly estados = [
    { valor: '', etiqueta: 'Todos los estados' },
    { valor: 'P', etiqueta: 'Pendiente' },
    { valor: 'V', etiqueta: 'Validado' },
    { valor: 'T', etiqueta: 'Traspasado a nómina' },
  ];

  public empleados: HeEmpleado[] = [];
  public trabajadoresDisponibles: HeEmpleado[] = [];
  public departamentos: string[] = [];
  public periodos: HePeriodo[] = [];
  public total = 0;
  public isLoading = false;
  public errorMessage = '';

  public ngOnInit() {
    this.cargar();
  }

  public cargar() {
    this.solicitud?.unsubscribe();
    this.isLoading = true;
    this.errorMessage = '';
    this.solicitud = this.heService.obtenerHorasPorEmpleado(this.anio, this.mesDesde, this.mesHasta, this.anioNatural, this.orden, {
      departamento: this.departamento,
      trabajador: this.trabajador,
      estado: this.estado,
      periodoId: this.periodo,
    }).pipe(
      takeUntil(this.destroy$),
      finalize(() => {
        this.isLoading = false;
        this.changeDetector.markForCheck();
      }),
    ).subscribe({
      next: (response) => {
        this.empleados = response.empleados || [];
        this.departamentos = response.departamentos || [];
        this.periodos = response.periodos || [];
        this.total = Number(response.total || 0);

        if (!this.trabajador && response.empleados) {
          this.trabajadoresDisponibles = response.empleados;
        }

        this.changeDetector.markForCheck();
      },
      error: (error) => {
        this.empleados = [];
        this.departamentos = [];
        this.total = 0;
        this.errorMessage = error?.error?.message || 'No se ha podido cargar el listado de horas por empleado.';
        this.changeDetector.markForCheck();
      },
    });
  }

  public cambiarAnio(valor: number) {
    this.anio = Number(valor);
    this.periodo = '';
    this.trabajador = '';
    this.cargar();
  }

  public nombreEmpleado(empleado: HeEmpleado) {
    return [empleado.nombre, empleado.apellidos].filter(Boolean).join(' ') || 'Sin nombre';
  }

  public ngOnDestroy() {
    this.solicitud?.unsubscribe();
    this.destroy$.next();
    this.destroy$.complete();
  }
}
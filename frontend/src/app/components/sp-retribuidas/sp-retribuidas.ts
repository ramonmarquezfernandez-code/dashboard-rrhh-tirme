import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, inject, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize, Subject, takeUntil } from 'rxjs';
import { HeService, SpDepartamento, SpPeriodoResumen, SpPersona } from '../../services/he.service';

@Component({
  selector: 'app-sp-retribuidas',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './sp-retribuidas.html',
  styleUrl: './sp-retribuidas.scss',
})
export class SpRetribuidas implements OnInit, OnDestroy {
  private readonly heService = inject(HeService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();

  public fechaHasta = this.fechaLocal(new Date());
  public periodo12?: SpPeriodoResumen;
  public periodo24?: SpPeriodoResumen;
  public personas12: SpPersona[] = [];
  public personas24: SpPersona[] = [];
  public departamentos12: SpDepartamento[] = [];
  public departamentos24: SpDepartamento[] = [];
  public isLoading = false;
  public errorMessage = '';
  public readonly colores = ['#2a9d8f', '#8ab17d', '#264653', '#e9c46a', '#f4a261', '#e76f51', '#6a994e', '#6d597a'];

  public ngOnInit() {
    this.cargar();
  }

  public cargar() {
    this.isLoading = true;
    this.errorMessage = '';
    this.heService.obtenerResumenSp(this.fechaHasta)
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.isLoading = false;
          this.changeDetector.markForCheck();
        }),
      )
      .subscribe({
        next: (response) => {
          this.periodo12 = this.normalizarPeriodo(response.periodos['12']);
          this.periodo24 = this.normalizarPeriodo(response.periodos['24']);
          this.personas12 = this.periodo12.personas;
          this.personas24 = this.periodo24.personas;
          this.departamentos12 = this.periodo12.departamentos;
          this.departamentos24 = this.periodo24.departamentos;
          this.changeDetector.markForCheck();
        },
        error: (error) => {
          this.periodo12 = undefined;
          this.periodo24 = undefined;
          this.personas12 = [];
          this.personas24 = [];
          this.departamentos12 = [];
          this.departamentos24 = [];
          this.errorMessage = error?.error?.message || 'No se ha podido cargar el resumen de SP.';
          this.changeDetector.markForCheck();
        },
      });
  }

  public nombrePersona(persona: SpPersona) {
    return [persona.nombre, persona.apellidos].filter(Boolean).join(' ') || persona.id;
  }

  private normalizarPeriodo(periodo: SpPeriodoResumen): SpPeriodoResumen {
    return {
      meses: Number(periodo?.meses || 0),
      fecha_desde: periodo?.fecha_desde || '',
      fecha_hasta: periodo?.fecha_hasta || '',
      total_sp: Number(periodo?.total_sp || 0),
      total_personas: Number(periodo?.total_personas || 0),
      personas: (periodo.personas || []).map((persona) => ({
        id: String(persona?.id || ''),
        nombre: persona.nombre || '',
        apellidos: persona.apellidos || '',
        departamento: persona.departamento || '',
        sp: Number(persona.sp || 0),
      })),
      departamentos: (periodo.departamentos || []).map((departamento) => ({
        departamento: departamento?.departamento || '',
        sp: Number(departamento?.sp || 0),
      })),
    };
  }

  public porcentaje(valor: number, total: number): number {
    return total > 0 ? (Number(valor || 0) / total) * 100 : 0;
  }

  public color(indice: number) {
    return this.colores[indice % this.colores.length];
  }

  public graficoDepartamentos(periodo: SpPeriodoResumen) {
    let acumulado = 0;
    const tramos = periodo.departamentos.map((item, indice) => {
      const inicio = acumulado;
      acumulado += (Number(item.sp || 0) / Math.max(periodo.total_sp, 1)) * 100;
      return `${this.color(indice)} ${inicio}% ${acumulado}%`;
    });
    return `conic-gradient(${tramos.join(', ')})`;
  }

  public tituloFecha(fecha: string) {
    return new Intl.DateTimeFormat('es-ES', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(`${fecha}T12:00:00`));
  }

  private fechaLocal(fecha: Date) {
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const dia = String(fecha.getDate()).padStart(2, '0');
    return `${fecha.getFullYear()}-${mes}-${dia}`;
  }

  public ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, inject, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize, Subject, Subscription, takeUntil } from 'rxjs';
import { HeEstado, HePeriodo, HeService, RankingComboFila, RankingComboResponse } from '../../services/he.service';

@Component({
  selector: 'app-ranking-combo',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ranking-combo.html',
  styleUrl: './ranking-combo.scss',
})
export class RankingCombo implements OnInit, OnDestroy {
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
  public periodos: HePeriodo[] = [];
  public estados: HeEstado[] = [{ valor: '', etiqueta: 'Todos' }];
  public departamentos: string[] = [];
  public filas: RankingComboFila[] = [];
  public trabajadoresDisponibles: RankingComboFila[] = [];
  public totales = { combo_programadas: 0, total_he: 0, he_compensables: 0, he_compensables_convertidas: 0 };
  public isLoading = false;
  public errorMessage = '';

  public ngOnInit() {
    this.cargarEstados();
    this.cargar();
  }

  private cargarEstados() {
    this.heService
      .obtenerEstados()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (estados) => {
          this.estados = [{ valor: '', etiqueta: 'Todos' }, ...(estados || [])];
          this.changeDetector.markForCheck();
        },
        error: () => {
          // Si falla la carga de estados, se mantiene únicamente la opción "Todos".
        },
      });
  }

  public cargar() {
    this.solicitud?.unsubscribe();
    this.isLoading = true;
    this.errorMessage = '';
    this.solicitud = this.heService.obtenerRankingCombo(this.anio, this.mesDesde, this.mesHasta, this.anioNatural, {
      departamento: this.departamento,
      trabajador: this.trabajador,
      estado: this.estado,
      periodoId: this.periodo,
    }).pipe(
      takeUntil(this.destroy$),
      finalize(() => { this.isLoading = false; this.changeDetector.markForCheck(); }),
    ).subscribe({
      next: (response: RankingComboResponse) => {
        this.filas = response.filas || [];
        this.totales = response.totales || this.totales;
        this.periodos = response.periodos || [];
        this.departamentos = response.departamentos || [];

        if (!this.trabajador && response.filas) {
          this.trabajadoresDisponibles = response.filas;
        }

        this.changeDetector.markForCheck();
      },
      error: (error) => {
        this.filas = [];
        this.errorMessage = error?.error?.message || 'No se ha podido cargar el ranking HE Combo.';
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

  public nombreEmpleado(fila: RankingComboFila) {
    return [fila.nombre, fila.apellidos].filter(Boolean).join(' ') || 'Sin nombre';
  }

  public maxGrafico() {
    return Math.max(...this.filas.map((fila) => Math.max(fila.he_compensables, fila.he_compensables_convertidas)), 1);
  }

  public rankingCombo() {
    return [...this.filas].sort((a, b) => b.combo_programadas - a.combo_programadas || a.pernr.localeCompare(b.pernr));
  }

  public rankingTotal() {
    return [...this.filas].sort((a, b) => b.total_he - a.total_he || a.pernr.localeCompare(b.pernr));
  }

  public rankingCompensar() {
    return [...this.filas].sort((a, b) => b.he_compensables - a.he_compensables || a.pernr.localeCompare(b.pernr));
  }

  public anchoGrafico(valor: number) {
    return `${(Number(valor || 0) / this.maxGrafico()) * 100}%`;
  }

  public ngOnDestroy() {
    this.solicitud?.unsubscribe();
    this.destroy$.next();
    this.destroy$.complete();
  }
}

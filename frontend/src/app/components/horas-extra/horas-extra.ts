import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, inject, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize, Subject, Subscription, takeUntil } from 'rxjs';
import { HeDepartamento, HeEstado, HeMensual, HePeriodo, HeService, HeTrabajador } from '../../services/he.service';

@Component({
  selector: 'app-horas-extra',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './horas-extra.html',
  styleUrl: './horas-extra.scss',
})
export class HorasExtra implements OnInit, OnDestroy {
  private readonly heService = inject(HeService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  public anio = 2026;
  public mesDesde = 1;
  public mesHasta = 12;
  public anioNatural = false;
  public departamento = '';
  public trabajador = '';
  public estado = '';
  public periodo = '';
  public departamentosDisponibles: string[] = [];
  public trabajadoresDisponibles: HeTrabajador[] = [];
  public periodos: HePeriodo[] = [];
  public estados: HeEstado[] = [{ valor: '', etiqueta: 'Todos los estados' }];
  public mensual: HeMensual[] = [];
  public departamentos: HeDepartamento[] = [];
  public trabajadores: HeTrabajador[] = [];
  public isLoading = false;
  public errorMessage = '';
  public readonly meses = Array.from({ length: 12 }, (_, index) => index + 1);
  public readonly coloresDepartamentos = [
    '#0f4c5c', '#e76f51', '#2a9d8f', '#f4a261',
    '#264653', '#e9c46a', '#6a994e', '#bc4749',
    '#457b9d', '#8d5a97', '#d1495b', '#00798c',
    '#edae49', '#30638e', '#758e4f', '#9c6644',
  ];
  private readonly destroy$ = new Subject<void>();
  private solicitudResumen?: Subscription;

  private readonly nombresMeses = [
    'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
    'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic',
  ];

  public ngOnInit() {
    this.cargarEstados();
    this.cargarResumen();
  }

  private cargarEstados() {
    this.heService
      .obtenerEstados()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (estados) => {
          this.estados = [{ valor: '', etiqueta: 'Todos los estados' }, ...(estados || [])];
          this.changeDetector.markForCheck();
        },
        error: () => {
          // Si falla, se mantiene la opción por defecto
        },
      });
  }

  public cargarResumen() {
    this.solicitudResumen?.unsubscribe();
    this.isLoading = true;
    this.errorMessage = '';

    this.heService.obtenerResumen(this.anio, this.mesDesde, this.mesHasta, this.anioNatural, {
      departamento: this.departamento,
      trabajador: this.trabajador,
      estado: this.estado,
      periodoId: this.periodo,
    })
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.isLoading = false;
          this.changeDetector.markForCheck();
        }),
      )
      .subscribe({
        next: (response) => {
          this.mensual = this.normalizarMensual(response?.mensual);
          this.departamentos = this.normalizarDepartamentos(response?.departamentos);
          this.trabajadores = this.normalizarTrabajadores(response?.trabajadores);
          this.periodos = response?.periodos || [];
          this.departamentosDisponibles = [...new Set(this.departamentos.map((item) => item.departamento).filter(Boolean) as string[])];
          this.trabajadoresDisponibles = this.trabajadores;
          this.changeDetector.markForCheck();
        },
        error: (error) => {
          this.mensual = [];
          this.departamentos = [];
          this.trabajadores = [];
          this.errorMessage = error?.error?.message || 'No se ha podido cargar el resumen de horas extra.';
          this.changeDetector.markForCheck();
        },
      });
  }

  public onFiltroChange(campo: 'anio' | 'mesDesde' | 'mesHasta', valor: number) {
    this[campo] = Number(valor);
    if (campo === 'anio') {
      this.periodo = '';
    }
    this.cargarResumen();
  }

  public onModoChange() {
    this.cargarResumen();
  }

  public onPeriodoChange(valor: string) {
    this.periodo = valor;
    this.cargarResumen();
  }

  public ngOnDestroy() {
    this.solicitudResumen?.unsubscribe();
    this.destroy$.next();
    this.destroy$.complete();
  }

  private normalizarNumero(valor: unknown): number {
    const numero = Number(valor ?? 0);
    return Number.isFinite(numero) ? numero : 0;
  }

  private normalizarMensual(items: HeMensual[] | null | undefined): HeMensual[] {
    return (Array.isArray(items) ? items : []).map((item) => ({
      mes: String(item?.mes ?? ''),
      normales: this.normalizarNumero(item?.normales),
      compensar: this.normalizarNumero(item?.compensar),
      busca: this.normalizarNumero(item?.busca),
      buscanp: this.normalizarNumero(item?.buscanp),
      combo: this.normalizarNumero(item?.combo),
      total: this.normalizarNumero(item?.total),
    }));
  }

  private normalizarDepartamentos(items: HeDepartamento[] | null | undefined): HeDepartamento[] {
    return (Array.isArray(items) ? items : []).map((item) => ({
      departamento: item?.departamento ?? 'Sin departamento',
      mes: String(item?.mes ?? ''),
      normales: this.normalizarNumero(item?.normales),
      compensar: this.normalizarNumero(item?.compensar),
      busca: this.normalizarNumero(item?.busca),
      buscanp: this.normalizarNumero(item?.buscanp),
      combo: this.normalizarNumero(item?.combo),
      total: this.normalizarNumero(item?.total),
    }));
  }

  private normalizarTrabajadores(items: HeTrabajador[] | null | undefined): HeTrabajador[] {
    return (Array.isArray(items) ? items : []).map((item) => ({
      id: String(item?.id ?? ''),
      nombre: item?.nombre ?? '',
      apellidos: item?.apellidos ?? '',
      departamento: item?.departamento ?? '-',
      mes: String(item?.mes ?? ''),
      normales: this.normalizarNumero(item?.normales),
      compensar: this.normalizarNumero(item?.compensar),
      busca: this.normalizarNumero(item?.busca),
      buscanp: this.normalizarNumero(item?.buscanp),
      combo: this.normalizarNumero(item?.combo),
      total: this.normalizarNumero(item?.total),
    }));
  }

  public nombreMes(mes: string) {
    return this.nombresMeses[Number(mes) - 1] || mes;
  }

  public nombreMesNumero(mes: number) {
    return this.nombresMeses[mes - 1] || '';
  }

  public totalHoras() {
    return this.mensual.reduce((total, item) => total + Number(item.total || 0), 0);
  }

  public trabajadoresSobreSetenta() {
    return this.trabajadores.filter((trabajador) => Number(trabajador.normales) > 70).length;
  }

  public departamentoPrincipal() {
    return this.departamentos[0]?.departamento || 'Sin datos';
  }

  public maxMensual() {
    return Math.max(...this.mensual.map((item) => Number(item.total || 0)), 1);
  }

  public maxDepartamento() {
    return Math.max(...this.departamentos.map((item) => Number(item.total || 0)), 1);
  }

  public totalDepartamentos() {
    return Math.max(this.departamentos.reduce((total, item) => total + this.normalizarNumero(item.total), 0), 1);
  }

  public porcentaje(valor: number, maximo: number) {
    return `${Math.max((Number(valor || 0) / maximo) * 100, 0)}%`;
  }

  public porcentajeTipo(valor: number, total: number) {
    return `${total > 0 ? (Number(valor || 0) / total) * 100 : 0}%`;
  }

  public nombreTrabajador(trabajador: HeTrabajador) {
    return [trabajador.nombre, trabajador.apellidos].filter(Boolean).join(' ') || trabajador.id;
  }

  public claseAlerta(total: number) {
    if (Number(total) >= 80) {
      return 'critico';
    }
    if (Number(total) > 70) {
      return 'advertencia';
    }
    return '';
  }

  public topTrabajadores() {
    return [...this.trabajadores].sort((a, b) => this.normalizarNumero(b.normales) - this.normalizarNumero(a.normales));
  }

  public segmentoCirculo(valor: number, total: number) {
    const circumference = 2 * Math.PI * 72;
    const segment = (this.normalizarNumero(valor) / Math.max(total, 1)) * circumference;
    return `${segment} ${circumference - segment}`;
  }

  public offsetCirculo(indice: number, total: number) {
    const circumference = 2 * Math.PI * 72;
    const acumulado = this.departamentos
      .slice(0, indice)
      .reduce((suma, item) => suma + this.normalizarNumero(item.total), 0);
    return (acumulado / Math.max(total, 1)) * circumference;
  }
}
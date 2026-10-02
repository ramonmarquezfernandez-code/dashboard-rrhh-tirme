import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface HeMensual {
  mes: string;
  normales: number;
  compensar: number;
  busca: number;
  buscanp: number;
  combo: number;
  total: number;
}

export interface HeDepartamento extends HeMensual {
  departamento: string | null;
}

export interface HeTrabajador extends HeMensual {
  nombre: string | null;
  apellidos: string | null;
  id: string;
  departamento: string | null;
}

export interface HePeriodoResponse {
  anio: string;
  mes_desde: number;
  mes_hasta: number;
  mensual: HeMensual[];
  departamentos: HeDepartamento[];
  trabajadores: HeTrabajador[];
  periodos: HePeriodo[];
}

export interface HePeriodo {
  id: string;
  ejercicio: string;
  descripcion: string;
  fecha_inicio: string | null;
  fecha_fin: string | null;
}

export interface HeEmpleado {
  pernr: string;
  nombre: string | null;
  apellidos: string | null;
  horas_extra: number;
}

export interface HeEmpleadosResponse {
  empleados: HeEmpleado[];
  departamentos: string[];
  total: number;
  periodos: HePeriodo[];
}

export interface RankingComboFila {
  pernr: string;
  nombre: string | null;
  apellidos: string | null;
  combo_programadas: number;
  total_he: number;
  he_compensables: number;
  he_compensables_convertidas: number;
}

export interface RankingComboResponse {
  filas: RankingComboFila[];
  departamentos: string[];
  totales: Omit<RankingComboFila, 'pernr' | 'nombre' | 'apellidos'>;
  periodos: HePeriodo[];
}

export interface SpPersona {
  nombre: string | null;
  apellidos: string | null;
  id: string;
  departamento: string | null;
  sp: number;
}

export interface SpDepartamento {
  departamento: string | null;
  sp: number;
}

export interface SpPeriodoResumen {
  meses: number;
  fecha_desde: string;
  fecha_hasta: string;
  personas: SpPersona[];
  departamentos: SpDepartamento[];
  total_sp: number;
  total_personas: number;
}

export interface SpResumenPeriodosResponse {
  fecha_hasta: string;
  periodos: { '12': SpPeriodoResumen; '24': SpPeriodoResumen };
}

export interface HeEstado {
  valor: string;
  etiqueta: string;
  color?: string;
}

export interface PlantillaGrupoResumen {
  nombre: string;
  total: number;
}

export interface PlantillaResumenResponse {
  total_plantilla: number;
  por_grupo: PlantillaGrupoResumen[];
  por_area: PlantillaGrupoResumen[];
  por_departamento: PlantillaGrupoResumen[];
}

@Injectable({ providedIn: 'root' })
export class HeService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = 'http://localhost:5000/api/partes';

  obtenerResumen(anio: number, mesDesde: number, mesHasta: number, anioNatural: boolean, filtros: { departamento?: string; trabajador?: string; estado?: string; periodoId?: string } = {}): Observable<HePeriodoResponse> {
    const params = new HttpParams()
      .set('anio', anio)
      .set('mes_desde', mesDesde)
      .set('mes_hasta', mesHasta)
      .set('anio_natural', anioNatural)
      .set('departamento', filtros.departamento || '')
      .set('pernr', filtros.trabajador || '')
      .set('estado', filtros.estado || '')
      .set('periodo_id', filtros.periodoId || '');

    return this.http.get<HePeriodoResponse>(`${this.apiUrl}/he-por-periodo`, { params });
  }

  obtenerHorasPorEmpleado(anio: number, mesDesde: number, mesHasta: number, anioNatural: boolean, orden: string, filtros: { departamento?: string; trabajador?: string; estado?: string; periodoId?: string } = {}): Observable<HeEmpleadosResponse> {
    const params = new HttpParams()
      .set('anio', anio)
      .set('mes_desde', mesDesde)
      .set('mes_hasta', mesHasta)
      .set('anio_natural', anioNatural)
      .set('orden', orden)
      .set('departamento', filtros.departamento || '')
      .set('pernr', filtros.trabajador || '')
      .set('estado', filtros.estado || '')
      .set('periodo_id', filtros.periodoId || '');

    return this.http.get<HeEmpleadosResponse>(`${this.apiUrl}/he-por-empleado`, { params });
  }

  obtenerRankingCombo(anio: number, mesDesde: number, mesHasta: number, anioNatural: boolean, filtros: { departamento?: string; trabajador?: string; estado?: string; periodoId?: string } = {}): Observable<RankingComboResponse> {
    const params = new HttpParams()
      .set('anio', anio).set('mes_desde', mesDesde).set('mes_hasta', mesHasta)
      .set('anio_natural', anioNatural)
      .set('departamento', filtros.departamento || '').set('pernr', filtros.trabajador || '')
      .set('estado', filtros.estado || '').set('periodo_id', filtros.periodoId || '');
    return this.http.get<RankingComboResponse>(`${this.apiUrl}/ranking-combo`, { params });
  }

  obtenerResumenSp(fechaHasta?: string): Observable<SpResumenPeriodosResponse> {
    let params = new HttpParams();
    if (fechaHasta) {
      params = params.set('fecha_hasta', fechaHasta);
    }
    return this.http.get<SpResumenPeriodosResponse>(`${this.apiUrl}/sp-resumen-periodos`, { params });
  }

  obtenerEstados(): Observable<HeEstado[]> {
    return this.http.get<HeEstado[]>(`${this.apiUrl}/estados`);
  }

  obtenerPlantillaResumen(filtros: { grupo?: string; direccion?: string } = {}): Observable<PlantillaResumenResponse> {
    const params = new HttpParams()
      .set('grupo', filtros.grupo || '')
      .set('direccion', filtros.direccion || '');
    return this.http.get<PlantillaResumenResponse>(`${this.apiUrl}/plantilla-resumen`, { params });
  }
}

import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './auth.service';

// Definición del formulario que sirve el backend (services/parte_campos.py)
export interface ConfiguracionParte {
  tramos: { clave: string; etiqueta: string; festivo: boolean }[];
  bloques: { clave: string; titulo: string; cuenta_en_total: boolean; es_recuento: boolean }[];
  situaciones: { clave: string; etiqueta: string }[];
  marcas: { clave: string; etiqueta: string }[];
  marca_sustitucion: string;
  turnos: { clave: string; etiqueta: string }[];
  festivos: [number, number][];
  limites: {
    max_total_he: number;
    max_horas_casilla: number;
    max_llamadas_casilla: number;
    max_km: number;
    max_texto: number;
  };
}

// Datos que envía el formulario
export interface DatosParte {
  fecha: string;
  turno: string;
  festivo_local: boolean;
  entrada: string;
  salida: string;
  pausa: string;
  horas: Record<string, Record<string, number | null>>;
  motivos: Record<string, string>;
  situacion: string;
  marcas: string[];
  motivo_sustitucion: string;
  km: number | null;
  observaciones: string;
}

// Parte guardado, en el formato del formulario
export interface Parte extends Omit<DatosParte, 'entrada' | 'salida' | 'pausa'> {
  mandt: number;
  tipodia: string;
  periodo: { mes: string; ejercicio: string };
  estado: string;
  editable: boolean;
  presencia_minutos: number | null;
  total_he: number;
}

export interface ResumenParte {
  mandt: number;
  fecha: string;
  turno: string;
  tipodia: string;
  estado: { valor: string; etiqueta: string; color: string | null };
  presencia: string | null;
  total_he: number;
  llamadas: number;
  editable: boolean;
}

@Injectable({ providedIn: 'root' })
export class PartesService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_URL}/mis-partes`;

  configuracion(): Observable<ConfiguracionParte> {
    return this.http.get<ConfiguracionParte>(`${this.url}/configuracion`);
  }

  listar(anio: number): Observable<{ ejercicio: string; partes: ResumenParte[] }> {
    return this.http.get<{ ejercicio: string; partes: ResumenParte[] }>(this.url, {
      params: new HttpParams().set('anio', anio),
    });
  }

  obtener(mandt: number): Observable<Parte> {
    return this.http.get<Parte>(`${this.url}/${mandt}`);
  }

  crear(datos: DatosParte): Observable<Parte> {
    return this.http.post<Parte>(this.url, datos);
  }

  actualizar(mandt: number, datos: DatosParte): Observable<Parte> {
    return this.http.put<Parte>(`${this.url}/${mandt}`, datos);
  }

  borrar(mandt: number): Observable<void> {
    return this.http.delete<void>(`${this.url}/${mandt}`);
  }
}

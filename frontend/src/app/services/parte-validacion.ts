// Reglas del formulario de parte en el navegador. Replican las del backend
// (services/parte_service.py, ParteValidator) para avisar al momento; el servidor
// vuelve a validar siempre y es quien decide.
import { ConfiguracionParte, DatosParte } from './partes.service';

const FORMATO_HORA = /^([01]\d|2[0-3]):([0-5]\d)$/;

export function minutos(hora: string): number {
  const [h, m] = hora.split(':').map(Number);
  return h * 60 + m;
}

/** Presencia en minutos (entrada a salida menos pausa); null si faltan datos o el formato no es válido.
 *  Si la salida es anterior, acaba al día siguiente; si es la misma hora, es una jornada de 24 h. */
export function presenciaMinutos(entrada: string, salida: string, pausa = '00:00'): number | null {
  if (!FORMATO_HORA.test(entrada || '') || !FORMATO_HORA.test(salida || '') || !FORMATO_HORA.test(pausa || '00:00')) {
    return null;
  }
  const duracion = (minutos(salida) - minutos(entrada) + 24 * 60) % (24 * 60) || 24 * 60;
  return duracion - minutos(pausa || '00:00');
}

export function formatoDuracion(totalMinutos: number | null): string {
  if (totalMinutos === null || totalMinutos === undefined) {
    return '—';
  }
  return `${Math.floor(totalMinutos / 60)} h ${String(totalMinutos % 60).padStart(2, '0')} min`;
}

/** L laborable, S sábado, D domingo, F festivo (como zparte.TIPODIA). */
export function tipoDia(fecha: string, festivos: [number, number][], festivoLocal = false): string {
  if (festivoLocal) {
    return 'F';
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha || '')) {
    return 'L';
  }
  const [anio, mes, dia] = fecha.split('-').map(Number);
  if (festivos.some(([d, m]) => d === dia && m === mes)) {
    return 'F';
  }
  const semana = new Date(anio, mes - 1, dia).getDay();
  return semana === 6 ? 'S' : semana === 0 ? 'D' : 'L';
}

export function sumaBloque(horas: Record<string, number | null> | undefined): number {
  return Object.values(horas || {}).reduce<number>((total, valor) => total + (Number(valor) || 0), 0);
}

export function totalHorasExtra(datos: DatosParte, config: ConfiguracionParte): number {
  return config.bloques
    .filter((bloque) => bloque.cuenta_en_total)
    .reduce((total, bloque) => total + sumaBloque(datos.horas[bloque.clave]), 0);
}

export function fechaIso(fecha: Date): string {
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return `${fecha.getFullYear()}-${mes}-${dia}`;
}

/** Errores por campo, con las mismas claves que devuelve el backend ('horas.normales.DF', 'motivos.busca'...). */
export function validarParte(
  datos: DatosParte,
  config: ConfiguracionParte,
  hoy: string,
  presenciaGuardada: number | null = null,
): Record<string, string> {
  const errores: Record<string, string> = {};
  const limites = config.limites;

  if (!/^\d{4}-\d{2}-\d{2}$/.test(datos.fecha || '')) {
    errores['fecha'] = 'Indica la fecha del parte.';
  } else if (datos.fecha > hoy) {
    errores['fecha'] = 'No se pueden registrar partes de días futuros.';
  }
  if (!config.turnos.some((turno) => turno.clave === datos.turno)) {
    errores['turno'] = 'Elige un turno.';
  }

  const festivo = tipoDia(datos.fecha, config.festivos, datos.festivo_local) !== 'L';
  for (const bloque of config.bloques) {
    const maximo = bloque.cuenta_en_total ? limites.max_horas_casilla : limites.max_llamadas_casilla;
    for (const tramo of config.tramos) {
      const valor = datos.horas[bloque.clave]?.[tramo.clave];
      const ruta = `horas.${bloque.clave}.${tramo.clave}`;
      if (valor === null || valor === undefined || (valor as unknown) === '') {
        continue;
      }
      if (!Number.isInteger(Number(valor))) {
        errores[ruta] = 'Debe ser un número entero.';
      } else if (valor < 0 || valor > maximo) {
        errores[ruta] = `Entre 0 y ${maximo}.`;
      } else if (valor > 0 && tramo.festivo && !festivo) {
        errores[ruta] = `${tramo.etiqueta}: solo en sábado, domingo o festivo.`;
      }
    }
    const motivo = (datos.motivos[bloque.clave] || '').trim();
    if (sumaBloque(datos.horas[bloque.clave]) > 0) {
      if (!motivo) {
        errores[`motivos.${bloque.clave}`] = `Indica el motivo de: ${bloque.titulo.toLowerCase()}.`;
      } else if (motivo.length > limites.max_texto) {
        errores[`motivos.${bloque.clave}`] = `Máximo ${limites.max_texto} caracteres.`;
      }
    }
  }

  const total = totalHorasExtra(datos, config);
  if (total > limites.max_total_he) {
    errores['total_he'] = `El total de horas extra (${total} h) supera el máximo de ${limites.max_total_he} h.`;
  }

  let presencia = presenciaGuardada;
  if (datos.entrada || datos.salida) {
    for (const campo of ['entrada', 'salida', 'pausa'] as const) {
      if (!FORMATO_HORA.test(datos[campo] || (campo === 'pausa' ? '00:00' : ''))) {
        errores[campo] = 'Formato HH:MM.';
      }
    }
    presencia = presenciaMinutos(datos.entrada, datos.salida, datos.pausa);
    if (presencia !== null && presencia <= 0) {
      errores['presencia'] = 'La presencia debe ser mayor que cero (revisa entrada, salida y pausa).';
    }
  }
  if (total > 0) {
    if (presencia === null) {
      errores['presencia'] ??= 'Si hay horas extra, indica la hora de entrada y de salida.';
    } else if (presencia > 0 && total * 60 > presencia) {
      errores['total_he'] ??= `Las horas extra (${total} h) no pueden superar el tiempo de presencia (${formatoDuracion(presencia)}).`;
    }
  }

  if (datos.km !== null && datos.km !== undefined && (datos.km as unknown) !== '') {
    if (!Number.isInteger(Number(datos.km)) || datos.km < 0 || datos.km > limites.max_km) {
      errores['km'] = `Entre 0 y ${limites.max_km}.`;
    } else if (datos.km > 0 && datos.situacion === 'teletrabajo') {
      errores['km'] = 'En teletrabajo no hay kilómetros de desplazamiento.';
    }
  }

  if (datos.marcas.includes(config.marca_sustitucion) && !(datos.motivo_sustitucion || '').trim()) {
    errores['motivo_sustitucion'] = 'Indica el motivo de la sustitución.';
  }
  if ((datos.observaciones || '').trim().length > limites.max_texto) {
    errores['observaciones'] = `Máximo ${limites.max_texto} caracteres.`;
  }
  return errores;
}

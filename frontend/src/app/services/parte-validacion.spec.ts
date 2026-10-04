import { ConfiguracionParte, DatosParte } from './partes.service';
import { formatoDuracion, presenciaMinutos, tipoDia, totalHorasExtra, validarParte } from './parte-validacion';

const CONFIG: ConfiguracionParte = {
  tramos: [
    { clave: 'DL', etiqueta: 'Diurna laborable', festivo: false },
    { clave: 'DF', etiqueta: 'Diurna festiva', festivo: true },
    { clave: 'NL', etiqueta: 'Nocturna laborable', festivo: false },
    { clave: 'NF', etiqueta: 'Nocturna festiva', festivo: true },
  ],
  bloques: [
    { clave: 'normales', titulo: 'Horas extra normales', cuenta_en_total: true, es_recuento: false },
    { clave: 'compensar', titulo: 'Horas extra a compensar', cuenta_en_total: true, es_recuento: false },
    { clave: 'llamadas', titulo: 'Llamadas (número)', cuenta_en_total: false, es_recuento: true },
  ],
  situaciones: [{ clave: 'ninguna', etiqueta: 'Ninguna' }, { clave: 'teletrabajo', etiqueta: 'Teletrabajo' }],
  marcas: [{ clave: 'SP', etiqueta: 'Superior categoría' }, { clave: 'SUST', etiqueta: 'Sustitución' }],
  marca_sustitucion: 'SUST',
  turnos: [{ clave: 'M', etiqueta: 'Mañana' }],
  festivos: [[1, 1], [12, 10]],
  limites: { max_total_he: 24, max_horas_casilla: 24, max_llamadas_casilla: 20, max_km: 1000, max_texto: 150 },
};
const HOY = '2026-10-07';

function datos(cambios: Partial<DatosParte> = {}): DatosParte {
  return {
    fecha: '2026-10-06', turno: 'M', festivo_local: false, entrada: '07:00', salida: '15:00', pausa: '00:00',
    horas: {}, motivos: {}, situacion: 'ninguna', marcas: [], motivo_sustitucion: '', km: null, observaciones: '',
    ...cambios,
  };
}

describe('parte-validacion', () => {
  it('calcula la presencia, también cruzando la medianoche', () => {
    expect(presenciaMinutos('07:00', '15:30', '00:30')).toBe(8 * 60);
    expect(presenciaMinutos('22:00', '06:00')).toBe(8 * 60);
    expect(presenciaMinutos('07:00', '07:00')).toBe(24 * 60);
    expect(presenciaMinutos('7:00', '15:00')).toBeNull();
    expect(formatoDuracion(485)).toBe('8 h 05 min');
  });

  it('calcula el tipo de día', () => {
    expect(tipoDia('2026-10-06', CONFIG.festivos)).toBe('L');
    expect(tipoDia('2026-10-04', CONFIG.festivos)).toBe('D');
    expect(tipoDia('2026-10-03', CONFIG.festivos)).toBe('S');
    expect(tipoDia('2026-10-12', CONFIG.festivos)).toBe('F');
    expect(tipoDia('2026-10-06', CONFIG.festivos, true)).toBe('F');
  });

  it('un parte correcto no tiene errores', () => {
    expect(validarParte(datos(), CONFIG, HOY)).toEqual({});
  });

  it('las llamadas no suman al total de horas extra', () => {
    const d = datos({ horas: { normales: { DL: 3 }, llamadas: { DL: 5 } } });
    expect(totalHorasExtra(d, CONFIG)).toBe(3);
  });

  it('24 horas extra se admiten y 25 no', () => {
    const base = { entrada: '00:00', salida: '00:00', motivos: { normales: 'a', compensar: 'b' } };
    expect(validarParte(datos({ ...base, horas: { normales: { DL: 12, NL: 12 } } }), CONFIG, HOY)['total_he']).toBeUndefined();
    const exceso = validarParte(datos({ ...base, horas: { normales: { DL: 20 }, compensar: { DL: 5 } } }), CONFIG, HOY);
    expect(exceso['total_he']).toContain('supera el máximo de 24');
  });

  it('cada bloque con horas exige su motivo', () => {
    const errores = validarParte(datos({ horas: { normales: { DL: 2 }, compensar: { NL: 1 } }, motivos: { normales: 'x' } }), CONFIG, HOY);
    expect(errores['motivos.compensar']).toBeTruthy();
    expect(errores['motivos.normales']).toBeUndefined();
  });

  it('las horas extra no pueden superar la presencia', () => {
    const errores = validarParte(datos({ salida: '09:00', horas: { normales: { DL: 3 } }, motivos: { normales: 'x' } }), CONFIG, HOY);
    expect(errores['total_he']).toContain('presencia');
  });

  it('tramos festivos solo en día no laborable', () => {
    const laborable = validarParte(datos({ horas: { normales: { DF: 2 } }, motivos: { normales: 'x' } }), CONFIG, HOY);
    expect(laborable['horas.normales.DF']).toBeTruthy();
    const domingo = validarParte(datos({ fecha: '2026-10-04', horas: { normales: { DF: 2 } }, motivos: { normales: 'x' } }), CONFIG, HOY);
    expect(domingo['horas.normales.DF']).toBeUndefined();
  });

  it('fecha futura, teletrabajo con km y sustitución sin motivo', () => {
    expect(validarParte(datos({ fecha: '2026-10-08' }), CONFIG, HOY)['fecha']).toContain('futuros');
    expect(validarParte(datos({ situacion: 'teletrabajo', km: 30 }), CONFIG, HOY)['km']).toContain('teletrabajo');
    expect(validarParte(datos({ marcas: ['SUST'] }), CONFIG, HOY)['motivo_sustitucion']).toBeTruthy();
  });
});

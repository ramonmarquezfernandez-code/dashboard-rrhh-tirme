import { puedeVerRuta, rutaInicio } from './permisos';

describe('permisos', () => {
  it('HR ve todas las pantallas', () => {
    for (const ruta of ['resumen-general', 'personal', 'turnos', 'horas-extra', 'ranking-combo', 'sp-retribuidas']) {
      expect(puedeVerRuta('hr', ruta)).toBe(true);
    }
  });

  it('un mando no ve Personal ni Turnos', () => {
    expect(puedeVerRuta('mando', 'resumen-general')).toBe(true);
    expect(puedeVerRuta('mando', 'ranking-combo')).toBe(true);
    expect(puedeVerRuta('mando', 'personal')).toBe(false);
    expect(puedeVerRuta('mando', 'turnos')).toBe(false);
  });

  it('un empleado solo ve sus pantallas de horas y SP', () => {
    expect(puedeVerRuta('empleado', 'horas-extra')).toBe(true);
    expect(puedeVerRuta('empleado', 'horas-extra-empleados')).toBe(true);
    expect(puedeVerRuta('empleado', 'sp-retribuidas')).toBe(true);
    expect(puedeVerRuta('empleado', 'resumen-general')).toBe(false);
    expect(puedeVerRuta('empleado', 'ranking-combo')).toBe(false);
  });

  it('sin sesión o con ruta desconocida no se ve nada', () => {
    expect(puedeVerRuta(null, 'horas-extra')).toBe(false);
    expect(puedeVerRuta('hr', 'no-existe')).toBe(false);
  });

  it('la pantalla de inicio depende del rol', () => {
    expect(rutaInicio('empleado')).toBe('/horas-extra');
    expect(rutaInicio('mando')).toBe('/resumen-general');
    expect(rutaInicio('hr')).toBe('/resumen-general');
  });
});

import { elegirAnio } from './he.service';

describe('elegirAnio', () => {
  it('usa los ejercicios de la API y el año actual que indica', () => {
    expect(elegirAnio({ ejercicios: ['2026', '2025', '2024'], actual: '2025' })).toEqual({
      anios: [2026, 2025, 2024],
      anio: 2025,
    });
  });

  it('si el actual no está en la lista, elige el más reciente', () => {
    expect(elegirAnio({ ejercicios: ['2026', '2025'], actual: '2030' }).anio).toBe(2026);
  });

  it('sin respuesta o sin ejercicios, usa el año en curso', () => {
    const anioEnCurso = new Date().getFullYear();
    expect(elegirAnio(null)).toEqual({ anios: [anioEnCurso], anio: anioEnCurso });
    expect(elegirAnio({ ejercicios: [], actual: '' })).toEqual({ anios: [anioEnCurso], anio: anioEnCurso });
  });

  it('descarta valores que no son años', () => {
    expect(elegirAnio({ ejercicios: ['2026', 'abc'], actual: '2026' }).anios).toEqual([2026]);
  });
});

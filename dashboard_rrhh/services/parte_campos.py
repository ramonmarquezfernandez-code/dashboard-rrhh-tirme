"""Definición del formulario de parte de trabajo: bloques de horas, marcas y límites.

Es la única fuente de verdad: el backend valida con ella y el frontend dibuja el
formulario a partir de GET /api/mis-partes/configuracion. Para cambiar el texto de
una marca basta con editar su etiqueta aquí.
"""
from services.calendario import FESTIVOS

# Tramos de cada bloque: prefijo de columna y etiqueta. Los festivos (F) solo se
# permiten en sábado, domingo o festivo.
TRAMOS = [
    ('DL', 'Diurna laborable', False),
    ('DF', 'Diurna festiva', True),
    ('NL', 'Nocturna laborable', False),
    ('NF', 'Nocturna festiva', True),
]

# Bloques: (clave, título, sufijo o prefijo de columna, columna del motivo, cuenta en el total de HE).
# Columnas de horas = tramo + sufijo (DL + 'C' = DLC); las llamadas usan 'LL' + tramo (LLDL).
BLOQUES = [
    ('normales', 'Horas extra normales', '', 'MOTIVOHE', True),
    ('compensar', 'Horas extra a compensar', 'C', 'MOTIVOHEC', True),
    ('busca', 'Horas de busca', 'B', 'MOTIVOHEB', True),
    ('busca_np', 'Horas de busca no pagada', 'BN', 'MOTHEBNP', True),
    ('combo', 'Horas combo', 'CO', 'MOTHECO', True),
    ('combo_prog', 'Horas combo programadas', 'COP', 'MOTHECOP', True),
    ('f', 'Horas F', 'F', 'MOTIVOHFM', True),
    ('llamadas', 'Llamadas (número)', 'LL', 'MOTIVOLLA', False),
]

# Situación del día: como máximo una. Se guarda 't' en la elegida y 'f' en las demás.
SITUACIONES = [
    ('ninguna', 'Ninguna', None),
    ('art21', 'Art. 21 descanso', 'ART21DESC'),
    ('descanso', 'Descanso', 'DESCANSO'),
    ('teletrabajo', 'Teletrabajo', 'TELETRABAJO'),
]

# Marcas de casilla: (columna, etiqueta). Se guardan como 'X' (marcada) o NULL,
# igual que en la tabla real. Completa aquí las etiquetas que falten.
MARCAS = [
    ('SP', 'Superior categoría'),
    ('SUST', 'Sustitución'),
    ('CP', 'CP'),
    ('PP', 'PP'),
    ('B', 'B'),
    ('D', 'D'),
    ('DD', 'DD'),
    ('P52', 'P52'),
    ('P60', 'P60'),
    ('BLV', 'BLV'),
    ('BSDF', 'BSDF'),
    ('CPT', 'CPT'),
    ('PN', 'PN'),
]
VALOR_MARCA = 'X'
MARCA_SUSTITUCION = 'SUST'

TURNOS = [('M', 'Mañana'), ('T', 'Tarde'), ('N', 'Noche'), ('D', 'D')]

# Límites
MAX_TOTAL_HE = 24          # horas extra totales por parte (todos los bloques salvo llamadas)
MAX_HORAS_CASILLA = 24
MAX_LLAMADAS_CASILLA = 20
MAX_KM = 1000
MAX_TEXTO = 150            # motivos y observaciones (varchar(150) en zparte)


def columna(bloque_sufijo, tramo):
    """Columna de zparte para un bloque y un tramo (p. ej. ('C', 'DL') -> 'DLC')."""
    return f'LL{tramo}' if bloque_sufijo == 'LL' else f'{tramo}{bloque_sufijo}'


def configuracion():
    """Definición del formulario para el frontend."""
    return {
        'tramos': [{'clave': t, 'etiqueta': e, 'festivo': f} for t, e, f in TRAMOS],
        'bloques': [
            {'clave': clave, 'titulo': titulo, 'cuenta_en_total': cuenta, 'es_recuento': not cuenta}
            for clave, titulo, _, _, cuenta in BLOQUES
        ],
        'situaciones': [{'clave': clave, 'etiqueta': etiqueta} for clave, etiqueta, _ in SITUACIONES],
        'marcas': [{'clave': c, 'etiqueta': e} for c, e in MARCAS],
        'marca_sustitucion': MARCA_SUSTITUCION,
        'turnos': [{'clave': c, 'etiqueta': e} for c, e in TURNOS],
        # Festivos fijos (día, mes) para calcular el tipo de día en el navegador
        'festivos': sorted([dia, mes] for dia, mes in FESTIVOS),
        'limites': {
            'max_total_he': MAX_TOTAL_HE, 'max_horas_casilla': MAX_HORAS_CASILLA,
            'max_llamadas_casilla': MAX_LLAMADAS_CASILLA, 'max_km': MAX_KM, 'max_texto': MAX_TEXTO,
        },
    }

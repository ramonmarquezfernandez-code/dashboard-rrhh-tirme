"""Cálculos de horas extra (HE) sobre zparte.

Columnas de horas: el prefijo indica el tramo (DL diurna laborable, DF diurna
festiva, NL nocturna laborable, NF nocturna festiva) y el sufijo el tipo.
"""
from datetime import date
from functools import reduce

from sqlalchemy import func

from extensions import db
from models import UserPayroll, ZParte
from services.filtro_partes import CatalogoPeriodos, FiltroPartesBuilder

TRAMOS = ('DL', 'DF', 'NL', 'NF')


def _columnas(sufijo):
    return tuple(f'{tramo}{sufijo}' for tramo in TRAMOS)


# Grupos de columnas por tipo de hora extra
NORMALES = _columnas('')            # DL, DF, NL, NF
COMPENSAR = _columnas('C')          # DLC, DFC, NLC, NFC
BUSCA = _columnas('B')              # DLB...
BUSCA_NP = _columnas('BN')          # DLBN... (busca no pagada)
COMBO = _columnas('CO')             # DLCO...
F = _columnas('F')                  # DLF...
COMBO_PROGRAMADAS = _columnas('COP')  # DLCOP...

# Dos definiciones de "total HE" que conviven a propósito (decisión del proyecto):
# - TOTAL_HE_PERIODO: pantallas de HE por periodo, por empleado y resúmenes (20 columnas).
# - TOTAL_HE_RANKING: Ranking HE Combo, que suma además F y combo programadas (28 columnas).
TOTAL_HE_PERIODO = NORMALES + COMPENSAR + BUSCA + BUSCA_NP + COMBO
TOTAL_HE_RANKING = TOTAL_HE_PERIODO + F + COMBO_PROGRAMADAS

# Conversión de horas compensables a horas de descanso, por tramo
COEFICIENTES_COMPENSABLES = {'DL': 1.6, 'DF': 2.0, 'NL': 2.0, 'NF': 2.5}

# Desglose que devuelven las pantallas de HE por periodo
DESGLOSE = {
    'normales': NORMALES,
    'compensar': COMPENSAR,
    'busca': BUSCA,
    'buscanp': BUSCA_NP,
    'combo': COMBO,
    'total': TOTAL_HE_PERIODO,
}


def suma_columnas(nombres):
    """Expresión SQL con la suma de varias columnas de ZParte."""
    return reduce(lambda acumulado, columna: acumulado + columna, (getattr(ZParte, n) for n in nombres))


def sumar(expresion):
    """SUM() que devuelve 0 en lugar de NULL cuando no hay filas."""
    return func.coalesce(func.sum(expresion), 0)


def _columnas_desglose():
    return [sumar(suma_columnas(columnas)).label(clave) for clave, columnas in DESGLOSE.items()]


def _enteros(fila, claves=DESGLOSE):
    """Convierte a int los totales (MariaDB devuelve Decimal en los SUM)."""
    return {clave: int(fila[clave] or 0) for clave in claves}


class HorasExtraService:
    """Consultas de horas extra limitadas por el filtro de perfil del usuario."""

    def __init__(self, filtro_perfil):
        self.filtro_perfil = filtro_perfil

    def _filtros(self, params, periodo=None):
        return (FiltroPartesBuilder(self.filtro_perfil)
                .periodo(params, periodo)
                .criterios(params)
                .construir())

    def _departamentos(self, filtros):
        return [
            fila[0] for fila in db.session.query(ZParte.DPTO)
            .filter(*filtros).filter(ZParte.DPTO.isnot(None))
            .distinct().order_by(ZParte.DPTO.asc()).all()
        ]

    # --- Ejercicios disponibles (combos de año) ------------------------------

    def ejercicios(self, hoy=None):
        """Ejercicios con partes visibles para el perfil más el año en curso, de más reciente a más antiguo.

        'actual' es el año en curso si tiene partes; si no, el más reciente con partes.
        """
        anio_en_curso = str((hoy or date.today()).year)
        con_datos = {
            fila[0] for fila in db.session.query(ZParte.EJERC)
            .filter(*FiltroPartesBuilder(self.filtro_perfil).construir(), ZParte.EJERC.isnot(None))
            .distinct().all()
        }
        ejercicios = sorted(con_datos | {anio_en_curso}, reverse=True)
        actual = anio_en_curso if anio_en_curso in con_datos or not con_datos else max(con_datos)
        return {'ejercicios': ejercicios, 'actual': actual}

    # --- Pantalla "HE por periodos" ------------------------------------------

    def por_periodo(self, params):
        catalogo = CatalogoPeriodos(params)
        periodo = catalogo.seleccionado()
        filtros = self._filtros(params, periodo)
        total = sumar(suma_columnas(TOTAL_HE_PERIODO))

        # Por periodo se agrupa por el mes de nómina (MES); por año natural, por el mes de la fecha
        mes = func.month(ZParte.PADAT) if params.anio_natural else ZParte.MES
        meses = [periodo.ID] if periodo is not None else params.meses()
        por_mes = {
            str(fila.mes).zfill(2): _enteros(fila._asdict())
            for fila in db.session.query(mes.label('mes'), *_columnas_desglose())
            .filter(*filtros).group_by(mes).all()
        }
        mensual = [{'mes': m, **por_mes.get(m, dict.fromkeys(DESGLOSE, 0))} for m in meses]

        departamentos = db.session.query(ZParte.DPTO.label('departamento'), *_columnas_desglose()) \
            .filter(*filtros).group_by(ZParte.DPTO).order_by(total.desc(), ZParte.DPTO.asc()).all()

        trabajadores = db.session.query(
            UserPayroll.NAME.label('nombre'),
            UserPayroll.SURNAME.label('apellidos'),
            ZParte.PERNR.label('id'),
            ZParte.DPTO.label('departamento'),
            *_columnas_desglose(),
        ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER) \
         .filter(*filtros) \
         .group_by(ZParte.PERNR, UserPayroll.NAME, UserPayroll.SURNAME, ZParte.DPTO) \
         .order_by(total.desc(), ZParte.PERNR.asc()).all()

        return {
            'anio': params.anio,
            'anio_natural': params.anio_natural,
            'periodo_id': params.periodo_id,
            'mes_desde': params.mes_desde,
            'mes_hasta': params.mes_hasta,
            'periodos': catalogo.serializar(),
            'mensual': mensual,
            'departamentos': [
                {'departamento': fila.departamento, **_enteros(fila._asdict())} for fila in departamentos
            ],
            'trabajadores': [
                {
                    'nombre': fila.nombre, 'apellidos': fila.apellidos,
                    'id': fila.id, 'departamento': fila.departamento,
                    **_enteros(fila._asdict()),
                }
                for fila in trabajadores
            ],
        }

    # --- Pantalla "HE por empleado" ------------------------------------------

    def por_empleado(self, params):
        catalogo = CatalogoPeriodos(params)
        filtros = self._filtros(params, catalogo.seleccionado())
        horas = sumar(suma_columnas(TOTAL_HE_PERIODO))

        consulta = db.session.query(
            ZParte.PERNR.label('pernr'),
            UserPayroll.NAME.label('nombre'),
            UserPayroll.SURNAME.label('apellidos'),
            horas.label('horas_extra'),
        ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER) \
         .filter(*filtros) \
         .group_by(ZParte.PERNR, UserPayroll.NAME, UserPayroll.SURNAME)
        if params.orden == 'pernr':
            consulta = consulta.order_by(ZParte.PERNR.asc())
        else:
            consulta = consulta.order_by(horas.desc(), ZParte.PERNR.asc())

        empleados = [
            {
                'pernr': fila.pernr, 'nombre': fila.nombre, 'apellidos': fila.apellidos,
                'horas_extra': int(fila.horas_extra or 0),
            }
            for fila in consulta.all()
        ]
        return {
            'anio': params.anio,
            'periodo_id': params.periodo_id,
            'orden': params.orden,
            'empleados': empleados,
            'departamentos': self._departamentos(filtros),
            'total': sum(empleado['horas_extra'] for empleado in empleados),
            'periodos': catalogo.serializar(),
        }

    # --- Pantalla "Ranking HE Combo" -----------------------------------------

    def ranking_combo(self, params):
        catalogo = CatalogoPeriodos(params)
        filtros = self._filtros(params, catalogo.seleccionado())
        total_he = suma_columnas(TOTAL_HE_RANKING)
        convertidas = reduce(
            lambda acumulado, termino: acumulado + termino,
            (getattr(ZParte, tramo) * coeficiente for tramo, coeficiente in COEFICIENTES_COMPENSABLES.items()),
        )

        consulta = db.session.query(
            ZParte.PERNR.label('pernr'),
            UserPayroll.NAME.label('nombre'),
            UserPayroll.SURNAME.label('apellidos'),
            sumar(suma_columnas(COMBO_PROGRAMADAS)).label('combo_programadas'),
            sumar(total_he).label('total_he'),
            sumar(suma_columnas(NORMALES)).label('he_compensables'),
            sumar(convertidas).label('he_compensables_convertidas'),
        ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER) \
         .filter(*filtros) \
         .group_by(ZParte.PERNR, UserPayroll.NAME, UserPayroll.SURNAME) \
         .order_by(func.sum(total_he).desc(), ZParte.PERNR.asc())

        filas = [
            {
                'pernr': fila.pernr, 'nombre': fila.nombre, 'apellidos': fila.apellidos,
                'combo_programadas': float(fila.combo_programadas or 0),
                'total_he': float(fila.total_he or 0),
                'he_compensables': float(fila.he_compensables or 0),
                'he_compensables_convertidas': round(float(fila.he_compensables_convertidas or 0), 2),
            }
            for fila in consulta.all()
        ]
        return {
            'anio': params.anio,
            'periodo_id': params.periodo_id,
            'filas': filas,
            'departamentos': self._departamentos(filtros),
            'totales': {
                'combo_programadas': sum(f['combo_programadas'] for f in filas),
                'total_he': sum(f['total_he'] for f in filas),
                'he_compensables': sum(f['he_compensables'] for f in filas),
                'he_compensables_convertidas': round(sum(f['he_compensables_convertidas'] for f in filas), 2),
            },
            'periodos': catalogo.serializar(),
        }

    # --- Resúmenes por ejercicio (sin pantalla en el frontend) ---------------

    def _filtros_ejercicio(self, anio):
        return FiltroPartesBuilder(self.filtro_perfil).ejercicio(anio).construir()

    def resumen_departamento(self, anio):
        filas = db.session.query(ZParte.DPTO.label('departamento'), *_columnas_desglose()) \
            .filter(*self._filtros_ejercicio(anio)).group_by(ZParte.DPTO).all()
        return [{'departamento': fila.departamento, **_enteros(fila._asdict())} for fila in filas]

    def resumen_trabajador(self, anio):
        retribuibles = sumar(suma_columnas(NORMALES + BUSCA)).label('totalretrib')
        filas = db.session.query(
            UserPayroll.NAME.label('trabajador'), ZParte.PERNR.label('id'),
            *_columnas_desglose(), retribuibles,
        ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER) \
         .filter(*self._filtros_ejercicio(anio)) \
         .group_by(ZParte.PERNR, UserPayroll.NAME).all()
        return [
            {'trabajador': fila.trabajador, 'id': fila.id,
             **_enteros(fila._asdict(), (*DESGLOSE, 'totalretrib'))}
            for fila in filas
        ]

    def comite(self, anio):
        filas = db.session.query(
            ZParte.PERNR.label('id_empleado'),
            sumar(suma_columnas(TOTAL_HE_PERIODO)).label('horas_extras'),
        ).filter(*self._filtros_ejercicio(anio)).group_by(ZParte.PERNR).all()
        return [{'id_empleado': fila.id_empleado, 'horas_extras': int(fila.horas_extras or 0)} for fila in filas]

    def anio_natural(self, anio):
        total = sumar(suma_columnas(TOTAL_HE_PERIODO))
        filas = db.session.query(
            UserPayroll.NAME.label('trabajador'), ZParte.PERNR.label('id'), total.label('total_he_anio'),
        ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER) \
         .filter(*self._filtros_ejercicio(anio)) \
         .group_by(ZParte.PERNR, UserPayroll.NAME) \
         .order_by(total.desc(), ZParte.PERNR.asc()).all()
        return [
            {'trabajador': fila.trabajador, 'id': fila.id, 'total_he_anio': int(fila.total_he_anio or 0)}
            for fila in filas
        ]

"""Servicios prestados (SP) registrados en los partes."""
import calendar
from datetime import date

from sqlalchemy import func

from extensions import db
from models import UserPayroll, ZParte
from services.filtro_partes import FiltroPartesBuilder, ParametroInvalido

# Las marcas de zparte (SP, SUST, BLV...) son char(1). En la explotación real
# (perfil estadístico, sin copiar registros) SP marcado vale 'X' y 'f' significa
# "no marcado". Se admiten también 't', '1' y 'S' por compatibilidad.
VALORES_MARCADO = ('t', 'X', '1', 'S')

VENTANAS_MESES = (12, 24)


def marcado(columna):
    """Condición SQL: la marca char(1) está activada ('f', '0', vacío y NULL no cuentan).

    Sin trim(): en CHAR(1) no aporta nada y una función sobre la columna impediría usar
    un índice (ver docs/rendimiento.md, índice propuesto sobre SP y PADAT)."""
    return columna.in_(VALORES_MARCADO)


def restar_meses(fecha, meses):
    """Misma fecha N meses antes (si el día no existe, el último día de ese mes)."""
    total_meses = fecha.year * 12 + fecha.month - 1 - meses
    anio, mes = divmod(total_meses, 12)
    dia = min(fecha.day, calendar.monthrange(anio, mes + 1)[1])
    return date(anio, mes + 1, dia)


def leer_fecha_hasta(texto):
    """Fecha final de la consulta (hoy si no se indica)."""
    texto = (texto or '').strip()
    if not texto:
        return date.today()
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ParametroInvalido('La fecha_hasta no es válida. Usa el formato YYYY-MM-DD.') from None


class SpService:
    """Recuento de SP por persona y departamento, limitado por el filtro de perfil."""

    def __init__(self, filtro_perfil):
        self.filtro_perfil = filtro_perfil

    def resumen_periodos(self, fecha_hasta):
        return {
            'fecha_hasta': fecha_hasta.isoformat(),
            'periodos': {str(meses): self._resumen(fecha_hasta, meses) for meses in VENTANAS_MESES},
        }

    def _resumen(self, fecha_hasta, meses):
        fecha_desde = restar_meses(fecha_hasta, meses)
        filtros = (FiltroPartesBuilder(self.filtro_perfil)
                   .rango_fechas(fecha_desde, fecha_hasta)
                   .condicion(marcado(ZParte.SP))
                   .construir())

        personas = (db.session.query(
            UserPayroll.NAME.label('nombre'),
            UserPayroll.SURNAME.label('apellidos'),
            ZParte.PERNR.label('id'),
            ZParte.DPTO.label('departamento'),
            func.count().label('sp'),
        ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)
            .filter(*filtros)
            .group_by(ZParte.PERNR, UserPayroll.NAME, UserPayroll.SURNAME, ZParte.DPTO)
            .order_by(func.count().desc(), ZParte.PERNR.asc()).all())

        departamentos = (db.session.query(ZParte.DPTO.label('departamento'), func.count().label('sp'))
                         .filter(*filtros)
                         .group_by(ZParte.DPTO)
                         .order_by(func.count().desc(), ZParte.DPTO.asc()).all())

        filas_personas = [{**fila._asdict(), 'sp': int(fila.sp)} for fila in personas]
        return {
            'meses': meses,
            'fecha_desde': fecha_desde.isoformat(),
            'fecha_hasta': fecha_hasta.isoformat(),
            'personas': filas_personas,
            'departamentos': [{'departamento': fila.departamento, 'sp': int(fila.sp)} for fila in departamentos],
            'total_sp': sum(persona['sp'] for persona in filas_personas),
            'total_personas': len(filas_personas),
        }

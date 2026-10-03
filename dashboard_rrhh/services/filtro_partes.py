"""Parámetros de consulta y filtros comunes sobre zparte.

Todas las pantallas filtran por el mismo conjunto de criterios (ejercicio,
rango de meses o año natural, periodo, departamento, trabajador y estado).
Aquí se validan los parámetros una sola vez y se construyen las condiciones,
siempre junto con el filtro de perfil del usuario (services/acceso.py).
"""
import calendar
from dataclasses import dataclass
from datetime import date

from extensions import db
from models import ZParte, ZPeriodos

ANIO_POR_DEFECTO = '2026'
VALORES_VERDADEROS = {'true', '1', 'si', 'yes'}


class ParametroInvalido(ValueError):
    """Parámetro de consulta no válido: la API responde 400 con este mensaje."""


@dataclass(frozen=True)
class ParametrosConsulta:
    anio: str = ANIO_POR_DEFECTO
    mes_desde: int = 1
    mes_hasta: int = 12
    anio_natural: bool = False
    periodo_id: str = ''
    departamento: str = ''
    pernr: str = ''
    estado: str = ''
    orden: str = 'horas'

    @staticmethod
    def leer_anio(texto):
        """Ejercicio de 4 cifras (por defecto ANIO_POR_DEFECTO)."""
        anio = (texto or ANIO_POR_DEFECTO).strip()
        if not (anio.isdigit() and len(anio) == 4):
            raise ParametroInvalido('El año no es válido.')
        return anio

    @classmethod
    def desde_args(cls, args):
        """Lee y valida los parámetros de la query string (request.args de Flask)."""
        anio = cls.leer_anio(args.get('anio'))

        mes_desde = max(args.get('mes_desde', 1, type=int), 1)
        mes_hasta = min(args.get('mes_hasta', 12, type=int), 12)
        if mes_desde > mes_hasta:
            raise ParametroInvalido('El periodo de meses no es válido.')

        return cls(
            anio=anio,
            mes_desde=mes_desde,
            mes_hasta=mes_hasta,
            anio_natural=str(args.get('anio_natural', 'false')).lower() in VALORES_VERDADEROS,
            periodo_id=(args.get('periodo_id') or '').strip(),
            departamento=(args.get('departamento') or '').strip(),
            pernr=(args.get('pernr') or '').strip(),
            estado=(args.get('estado') or '').strip(),
            orden='pernr' if (args.get('orden') or '').lower() == 'pernr' else 'horas',
        )

    def meses(self):
        """Meses del rango como texto de dos cifras ('01'..'12')."""
        return [f'{mes:02d}' for mes in range(self.mes_desde, self.mes_hasta + 1)]

    def rango_fechas(self):
        """Primer y último día del rango de meses (consultas por año natural)."""
        anio = int(self.anio)
        ultimo_dia = calendar.monthrange(anio, self.mes_hasta)[1]
        return date(anio, self.mes_desde, 1), date(anio, self.mes_hasta, ultimo_dia)


class CatalogoPeriodos:
    """Periodos de nómina (zperiodos) de un ejercicio."""

    def __init__(self, params):
        self.params = params
        self.periodos = db.session.scalars(
            db.select(ZPeriodos).where(ZPeriodos.EJERCICIO == params.anio).order_by(ZPeriodos.ID)
        ).all()

    def seleccionado(self):
        """Periodo elegido con periodo_id, o None si no se eligió o se consulta por año natural."""
        if not self.params.periodo_id or self.params.anio_natural:
            return None
        periodo = next((p for p in self.periodos if p.ID == self.params.periodo_id), None)
        if periodo is None:
            raise ParametroInvalido('El periodo seleccionado no existe para el ejercicio indicado.')
        return periodo

    def serializar(self):
        return [
            {
                'id': periodo.ID,
                'ejercicio': periodo.EJERCICIO,
                'descripcion': periodo.DESCRIPTION or f'Periodo {periodo.ID}',
                'fecha_inicio': periodo.FECHAINI.isoformat() if periodo.FECHAINI else None,
                'fecha_fin': periodo.FECHAFIN.isoformat() if periodo.FECHAFIN else None,
            }
            for periodo in self.periodos
        ]


class FiltroPartesBuilder:
    """Construye la lista de condiciones para .filter(*condiciones) sobre ZParte.

    Siempre incluye el filtro de perfil; los criterios vacíos se ignoran.

        condiciones = (FiltroPartesBuilder(usuario.filtro_partes())
                       .periodo(params, periodo).departamento('Operaciones')
                       .construir())
    """

    def __init__(self, filtro_perfil):
        self._condiciones = [filtro_perfil]

    def periodo(self, params, periodo=None):
        """Aplica uno de los tres modos de periodo:

        - año natural: por fecha del parte (PADAT) dentro del rango de meses;
        - periodo de nómina seleccionado: ejercicio + MES del periodo;
        - por defecto: ejercicio + MES dentro del rango de meses.
        """
        if params.anio_natural:
            return self.rango_fechas(*params.rango_fechas())
        if periodo is not None:
            self._condiciones += [ZParte.EJERC == periodo.EJERCICIO, ZParte.MES == periodo.ID]
            return self
        self._condiciones += [ZParte.EJERC == params.anio, ZParte.MES.in_(params.meses())]
        return self

    def criterios(self, params):
        """Departamento, trabajador y estado de los parámetros."""
        return self.departamento(params.departamento).pernr(params.pernr).estado(params.estado)

    def ejercicio(self, anio):
        return self.condicion(ZParte.EJERC == anio) if anio else self

    def rango_fechas(self, desde, hasta):
        return self.condicion(ZParte.PADAT.between(desde, hasta))

    def departamento(self, departamento):
        return self.condicion(ZParte.DPTO == departamento) if departamento else self

    def pernr(self, pernr):
        return self.condicion(ZParte.PERNR == pernr) if pernr else self

    def estado(self, estado):
        return self.condicion(ZParte.STAT == estado) if estado else self

    def condicion(self, expresion):
        self._condiciones.append(expresion)
        return self

    def construir(self):
        return list(self._condiciones)

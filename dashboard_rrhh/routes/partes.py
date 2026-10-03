"""Endpoints de partes de horas (/api/partes), documentados en Swagger (/api/doc).

Las rutas solo leen parámetros, comprueban el perfil y delegan en los servicios.
Todos los datos se limitan con el filtro de perfil del usuario (services/acceso.py).
"""
from flask import request
from flask_restx import Namespace, Resource

from extensions import db
from models import EppartStatus, ZParte
from schemas.parte_schema import partes_schema
from services.acceso import filtro_partes, filtro_plantilla, requiere_rol
from services.filtro_partes import ANIO_POR_DEFECTO, FiltroPartesBuilder, ParametroInvalido, ParametrosConsulta
from services.horas_extra_service import HorasExtraService
from services.plantilla_service import PlantillaService
from services.rol_service import ROL_HR, ROL_MANDO
from services.sp_service import SpService, leer_fecha_hasta

partes_ns = Namespace('partes', description='Partes de horas, horas extra, SP y plantilla')

PARAM_ANIO = {'anio': f'Ejercicio, p. ej. {ANIO_POR_DEFECTO}'}
PARAMS_CONSULTA = {
    **PARAM_ANIO,
    'mes_desde': 'Primer mes (1-12)',
    'mes_hasta': 'Último mes (1-12)',
    'anio_natural': 'true: filtra por fecha del parte en lugar de por mes de nómina',
    'periodo_id': 'Periodo de nómina (zperiodos.ID); se ignora con anio_natural',
    'departamento': 'Departamento (zparte.DPTO)',
    'pernr': 'Número de personal',
    'estado': 'Estado del parte (eppartstatus.STATUS)',
}


@partes_ns.errorhandler(ParametroInvalido)
def parametro_invalido(error):
    return {'message': str(error)}, 400


def _anio():
    return ParametrosConsulta.leer_anio(request.args.get('anio'))


# --- Catálogo y partes -------------------------------------------------------

@partes_ns.route('/estados')
class Estados(Resource):
    @requiere_rol()
    @partes_ns.doc(security='Bearer')
    def get(self):
        """Estados posibles de un parte (combos de filtro)."""
        estados = db.session.scalars(db.select(EppartStatus).order_by(EppartStatus.STATUS)).all()
        return [{'valor': e.STATUS, 'etiqueta': e.DESCRIPTION, 'color': e.COLOR} for e in estados]


@partes_ns.route('')
class Listado(Resource):
    @requiere_rol()
    @partes_ns.doc(security='Bearer', params={'page': 'Página (1 por defecto)', 'per_page': 'Resultados por página (20)'})
    def get(self):
        """Listado paginado de partes visibles para el perfil."""
        paginacion = ZParte.query.filter(filtro_partes()).paginate(
            page=request.args.get('page', 1, type=int),
            per_page=request.args.get('per_page', 20, type=int),
            error_out=False,
        )
        return {
            'total': paginacion.total,
            'pages': paginacion.pages,
            'current_page': paginacion.page,
            'partes': partes_schema.dump(paginacion.items),
        }


@partes_ns.route('/empleado/<string:pernr>')
class PartesEmpleado(Resource):
    @requiere_rol()
    @partes_ns.doc(security='Bearer')
    def get(self, pernr):
        """Partes de un trabajador (404 si no existen o no son visibles para el perfil)."""
        condiciones = FiltroPartesBuilder(filtro_partes()).pernr(pernr).construir()
        partes = ZParte.query.filter(*condiciones).all()
        if not partes:
            return {'message': f'No se encontraron partes para el empleado {pernr}'}, 404
        return partes_schema.dump(partes)


# --- Pantallas del frontend --------------------------------------------------

@partes_ns.route('/he-por-periodo')
class HePorPeriodo(Resource):
    @requiere_rol()
    @partes_ns.doc(security='Bearer', params=PARAMS_CONSULTA)
    def get(self):
        """HE por periodos: desglose mensual, por departamento y por trabajador."""
        return HorasExtraService(filtro_partes()).por_periodo(ParametrosConsulta.desde_args(request.args))


@partes_ns.route('/he-por-empleado')
class HePorEmpleado(Resource):
    @requiere_rol()
    @partes_ns.doc(security='Bearer', params={**PARAMS_CONSULTA, 'orden': "'horas' (por defecto) o 'pernr'"})
    def get(self):
        """Total de HE por trabajador."""
        return HorasExtraService(filtro_partes()).por_empleado(ParametrosConsulta.desde_args(request.args))


@partes_ns.route('/ranking-combo')
class RankingCombo(Resource):
    @requiere_rol(ROL_HR, ROL_MANDO)
    @partes_ns.doc(security='Bearer', params=PARAMS_CONSULTA)
    def get(self):
        """Ranking HE combo: totales, HE compensables y su conversión a descanso."""
        return HorasExtraService(filtro_partes()).ranking_combo(ParametrosConsulta.desde_args(request.args))


@partes_ns.route('/sp-resumen-periodos')
class SpResumenPeriodos(Resource):
    @requiere_rol()
    @partes_ns.doc(security='Bearer', params={'fecha_hasta': 'Fecha final YYYY-MM-DD (hoy por defecto)'})
    def get(self):
        """SP de los últimos 12 y 24 meses por persona y departamento."""
        fecha_hasta = leer_fecha_hasta(request.args.get('fecha_hasta'))
        return SpService(filtro_partes()).resumen_periodos(fecha_hasta)


@partes_ns.route('/plantilla-resumen')
class PlantillaResumen(Resource):
    @requiere_rol(ROL_HR, ROL_MANDO)
    @partes_ns.doc(security='Bearer', params={'grupo': "Nombre de grupo o 'TODOS'", 'direccion': "Nombre de área o 'TODAS'"})
    def get(self):
        """Empleados activos: total y desglose por grupo, área y departamento."""
        return PlantillaService(filtro_plantilla()).resumen(
            grupo=(request.args.get('grupo') or '').strip(),
            direccion=(request.args.get('direccion') or '').strip(),
        )


# --- Resúmenes por ejercicio -------------------------------------------------

@partes_ns.route('/resumen-departamento')
class ResumenDepartamento(Resource):
    @requiere_rol()
    @partes_ns.doc(security='Bearer', params=PARAM_ANIO)
    def get(self):
        """HE del ejercicio por departamento."""
        return HorasExtraService(filtro_partes()).resumen_departamento(_anio())


@partes_ns.route('/resumen-trabajador')
class ResumenTrabajador(Resource):
    @requiere_rol()
    @partes_ns.doc(security='Bearer', params=PARAM_ANIO)
    def get(self):
        """HE del ejercicio por trabajador, con el total retribuible (normales + busca)."""
        return HorasExtraService(filtro_partes()).resumen_trabajador(_anio())


@partes_ns.route('/comite')
class Comite(Resource):
    @requiere_rol()
    @partes_ns.doc(security='Bearer', params=PARAM_ANIO)
    def get(self):
        """Total de HE del ejercicio por trabajador (informe para el comité)."""
        return HorasExtraService(filtro_partes()).comite(_anio())


@partes_ns.route('/he-anio-natural')
class HeAnioNatural(Resource):
    @requiere_rol()
    @partes_ns.doc(security='Bearer', params=PARAM_ANIO)
    def get(self):
        """Total de HE del ejercicio por trabajador, de mayor a menor."""
        return HorasExtraService(filtro_partes()).anio_natural(_anio())

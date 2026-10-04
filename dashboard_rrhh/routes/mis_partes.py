"""Partes de trabajo del propio empleado (/api/mis-partes): alta, consulta, edición y borrado.

Disponible para todos los perfiles; cada usuario solo ve y modifica sus partes
(el PERNR sale siempre del token).
"""
from flask import request
from flask_restx import Namespace, Resource

from services import parte_campos
from services.acceso import requiere_rol, usuario_actual
from services.filtro_partes import ParametrosConsulta
from services.parte_service import ConflictoParte, ErrorValidacion, ParteNoEncontrado, ParteService

mis_partes_ns = Namespace('mis-partes', description='Partes de trabajo del propio empleado')


@mis_partes_ns.errorhandler(ErrorValidacion)
def error_validacion(error):
    return {'message': str(error), 'errores': error.errores}, 400


@mis_partes_ns.errorhandler(ConflictoParte)
def conflicto(error):
    return {'message': str(error)}, 409


@mis_partes_ns.errorhandler(ParteNoEncontrado)
def no_encontrado(error):
    return {'message': str(error)}, 404


def _servicio():
    return ParteService(usuario_actual())


@mis_partes_ns.route('/configuracion')
class Configuracion(Resource):
    @requiere_rol()
    @mis_partes_ns.doc(security='Bearer')
    def get(self):
        """Definición del formulario: bloques de horas, tramos, situaciones, marcas, turnos y límites."""
        return parte_campos.configuracion()


@mis_partes_ns.route('')
class MisPartes(Resource):
    @requiere_rol()
    @mis_partes_ns.doc(security='Bearer', params={'anio': 'Ejercicio (por defecto, el año en curso)'})
    def get(self):
        """Mis partes de un ejercicio, con su estado y si aún se pueden modificar."""
        from datetime import date

        anio = ParametrosConsulta.leer_anio(request.args.get('anio') or str(date.today().year))
        return _servicio().listar(anio)

    @requiere_rol()
    @mis_partes_ns.doc(security='Bearer')
    def post(self):
        """Crea un parte del usuario (estado B, creado por el empleado)."""
        return _servicio().crear(request.get_json(silent=True) or {}), 201


@mis_partes_ns.route('/<int:mandt>')
class MiParte(Resource):
    @requiere_rol()
    @mis_partes_ns.doc(security='Bearer')
    def get(self, mandt):
        """Un parte propio en el formato del formulario."""
        return _servicio().obtener(mandt)

    @requiere_rol()
    @mis_partes_ns.doc(security='Bearer')
    def put(self, mandt):
        """Modifica un parte propio mientras siga en estado B."""
        return _servicio().actualizar(mandt, request.get_json(silent=True) or {})

    @requiere_rol()
    @mis_partes_ns.doc(security='Bearer')
    def delete(self, mandt):
        """Borra un parte propio mientras siga en estado B."""
        _servicio().borrar(mandt)
        return '', 204

"""Control de accesos: usuario actual del JWT, decorador @requiere_rol y
filtros de datos según el rol activo. Todo el filtrado se aplica aquí, en el
backend; el frontend solo oculta menús."""
from dataclasses import dataclass, field
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from sqlalchemy import false, or_, true

from models import UserPayroll, ZParte
from services.rol_service import PRIORIDAD_ROLES, ROL_EMPLEADO, ROL_HR, ROL_MANDO

TODOS_LOS_ROLES = PRIORIDAD_ROLES


@dataclass(frozen=True)
class UsuarioActual:
    pernr: str
    email: str
    rol_activo: str
    codgrs: frozenset = field(default_factory=frozenset)

    @classmethod
    def desde_jwt(cls):
        claims = get_jwt()
        return cls(
            pernr=claims['sub'],
            email=claims.get('email', ''),
            rol_activo=claims.get('rol_activo', ROL_EMPLEADO),
            codgrs=frozenset(claims.get('codgrs') or []),
        )

    def filtro_partes(self):
        """Condición sobre ZParte que limita los partes visibles."""
        if self.rol_activo == ROL_HR:
            return true()
        if self.rol_activo == ROL_MANDO:
            condiciones = [ZParte.PERNR == self.pernr]
            if self.codgrs:
                condiciones.append(ZParte.CODGR.in_(self.codgrs))
            return or_(*condiciones)
        if self.rol_activo == ROL_EMPLEADO:
            return ZParte.PERNR == self.pernr
        return false()

    def filtro_plantilla(self):
        """Condición sobre UserPayroll que limita los trabajadores visibles."""
        if self.rol_activo == ROL_HR:
            return true()
        if self.rol_activo == ROL_MANDO:
            condiciones = [UserPayroll.NUMPER == self.pernr]
            if self.codgrs:
                condiciones.append(UserPayroll.GRUPO.in_(self.codgrs))
            return or_(*condiciones)
        if self.rol_activo == ROL_EMPLEADO:
            return UserPayroll.NUMPER == self.pernr
        return false()


def usuario_actual():
    """Usuario autenticado de la petición en curso (requiere JWT verificado)."""
    return UsuarioActual.desde_jwt()


def filtro_partes():
    return usuario_actual().filtro_partes()


def filtro_plantilla():
    return usuario_actual().filtro_plantilla()


def requiere_rol(*roles_permitidos):
    """Exige un JWT válido y que el rol activo esté entre los permitidos.

    Sin token o con token inválido -> 401 (lo gestiona flask-jwt-extended).
    Rol activo no permitido        -> 403.
    """
    roles_permitidos = roles_permitidos or TODOS_LOS_ROLES

    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            verify_jwt_in_request()
            if usuario_actual().rol_activo not in roles_permitidos:
                # Se devuelve un Response (no una tupla) para que funcione igual
                # en blueprints de Flask y en recursos de Flask-RESTX
                respuesta = jsonify({'message': 'Tu perfil no tiene acceso a este recurso.'})
                respuesta.status_code = 403
                return respuesta
            return funcion(*args, **kwargs)
        return envoltura
    return decorador

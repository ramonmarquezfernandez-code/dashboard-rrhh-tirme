from flask import request
from flask_restx import Namespace, Resource, fields

from services.acceso import requiere_rol, usuario_actual
from services.auth_service import AuthService
from services.rol_service import RolService

# Namespace montado en /api (mismas URLs que usa el frontend Angular)
auth_ns = Namespace('auth', description='Autenticación (bcrypt + JWT) y roles del usuario')

MENSAJE_CREDENCIALES = 'Correo o contraseña incorrectos.'

get_roles_model = auth_ns.model('GetRolesRequest', {
    'email': fields.String(required=True, description='Correo del usuario'),
    'password': fields.String(required=True, description='Contraseña'),
})

login_model = auth_ns.model('LoginRequest', {
    'email': fields.String(required=True, description='Correo del usuario'),
    'password': fields.String(required=True, description='Contraseña'),
    'rol': fields.String(description="Rol activo: 'hr', 'mando' o 'empleado' (por defecto, el de mayor prioridad)"),
})


def _datos_usuario(usuario, rol, roles):
    return {
        'email': (usuario.EMAIL or '').lower(),
        'pernr': usuario.NUMPER,
        'nombre': ' '.join(filter(None, [usuario.NAME, usuario.SURNAME])),
        'rolActivo': rol,
        'roles': roles,
    }


@auth_ns.route('/get-roles')
class GetRoles(Resource):
    @auth_ns.expect(get_roles_model)
    def post(self):
        """Valida las credenciales y devuelve los roles del usuario (siempre incluye 'empleado').

        Exige la contraseña para no revelar qué correos existen ni qué perfiles tienen.
        """
        data = request.get_json(silent=True) or {}
        if not str(data.get('email') or '').strip():
            auth_ns.abort(400, 'El correo es obligatorio')

        usuario = AuthService.buscar_usuario_activo(data['email'])
        if not AuthService.verificar_password(usuario, data.get('password')):
            auth_ns.abort(401, MENSAJE_CREDENCIALES)

        return {'success': True, 'roles': RolService(usuario.NUMPER).roles_disponibles()}, 200


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        """Valida credenciales y rol elegido y devuelve un JWT."""
        data = request.get_json(silent=True) or {}
        if not str(data.get('email') or '').strip():
            auth_ns.abort(400, 'El correo es obligatorio')

        usuario = AuthService.buscar_usuario_activo(data['email'])
        if not AuthService.verificar_password(usuario, data.get('password')):
            auth_ns.abort(401, MENSAJE_CREDENCIALES)

        # El servidor comprueba que el usuario posee el rol que ha elegido
        rol_service = RolService(usuario.NUMPER)
        rol = data.get('rol') or rol_service.rol_por_defecto()
        if not rol_service.tiene_rol(rol):
            auth_ns.abort(403, 'No tienes asignado el perfil seleccionado.')

        return {
            'success': True,
            'token': AuthService.emitir_token(usuario, rol, rol_service),
            'user': _datos_usuario(usuario, rol, rol_service.roles_disponibles()),
        }, 200


@auth_ns.route('/me')
class Me(Resource):
    @auth_ns.doc(security='Bearer')
    @requiere_rol()
    def get(self):
        """Datos de la sesión actual según el JWT."""
        actual = usuario_actual()
        return {
            'success': True,
            'user': {
                'email': actual.email,
                'pernr': actual.pernr,
                'rolActivo': actual.rol_activo,
                'codgrs': sorted(actual.codgrs),
            },
        }, 200

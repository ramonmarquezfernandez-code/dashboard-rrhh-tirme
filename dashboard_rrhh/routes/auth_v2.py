from flask_restx import Namespace, Resource, fields
from flask import request, jsonify

# Crear un namespace para autenticación
auth_ns = Namespace('auth', description='Autenticación y gestión de usuarios')

# Modelos para documentación Swagger
login_model = auth_ns.model(
    'Login',
    {
        'email': fields.String(required=True, description='Correo del usuario'),
        'password': fields.String(required=True, description='Contraseña'),
        'rol': fields.String(description='Rol seleccionado (default: empleado)'),
    }
)

login_response_model = auth_ns.model(
    'LoginResponse',
    {
        'success': fields.Boolean(description='Indica si el login fue exitoso'),
        'user': fields.Raw(description='Datos del usuario autenticado'),
        'token': fields.String(description='Token JWT (futuro)'),
    }
)

roles_model = auth_ns.model(
    'RolesResponse',
    {
        'success': fields.Boolean(description='Indica si la operación fue exitosa'),
        'roles': fields.List(fields.String, description='Lista de roles disponibles'),
    }
)


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('login_usuario')
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(login_response_model)
    def post(self):
        """
        Autentica un usuario y devuelve su información.
        
        Parámetros requeridos:
        - email: correo del usuario
        - password: contraseña
        - rol (opcional): rol a activar (default: 'empleado')
        """
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')
        rol_seleccionado = data.get('rol', 'empleado')

        if not email or not password:
            auth_ns.abort(400, 'Faltan credenciales obligatorias')

        # TODO: Validar contra la BD con contraseña hasheada
        # TODO: Verificar que el usuario tiene el rol seleccionado

        return {
            'success': True,
            'user': {
                'email': email,
                'rolActivo': rol_seleccionado,
                'nombre': 'Usuario Demo',
            },
            'token': 'token_jwt_aqui',
        }, 200


@auth_ns.route('/get-roles')
class GetRoles(Resource):
    @auth_ns.doc('get_roles_usuario')
    @auth_ns.expect(auth_ns.model(
        'GetRolesRequest',
        {'email': fields.String(required=True, description='Correo del usuario')}
    ))
    @auth_ns.marshal_with(roles_model)
    def post(self):
        """
        Obtiene los roles disponibles para un usuario.
        """
        data = request.get_json() or {}
        email = data.get('email')

        if not email:
            auth_ns.abort(400, 'El correo es obligatorio')

        # TODO: Consultar roles reales de la BD
        # Simulación temporal
        return {
            'success': True,
            'roles': ['empleado', 'hr', 'manager'],
        }, 200


@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc('logout_usuario')
    def post(self):
        """
        Cierra la sesión del usuario.
        """
        return {
            'success': True,
            'message': 'Sesión cerrada correctamente',
        }, 200


@auth_ns.route('/me')
class GetCurrentUser(Resource):
    @auth_ns.doc('get_current_user')
    def get(self):
        """
        Obtiene la información del usuario actual autenticado.
        """
        # TODO: Obtener usuario del token JWT
        return {
            'success': True,
            'user': {
                'email': 'usuario@ejemplo.com',
                'nombre': 'Usuario Demo',
                'rolActivo': 'empleado',
            }
        }, 200

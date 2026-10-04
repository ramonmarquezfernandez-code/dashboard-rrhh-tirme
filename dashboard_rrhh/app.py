import os

from config import Config
from extensions import db, jwt, ma
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api

# Namespaces de la API (todos documentados en Swagger)
from routes.auth import auth_ns
from routes.mis_partes import mis_partes_ns
from routes.partes import partes_ns


def index():
    return jsonify(
        {
            'status': 'online',
            'message': 'Dashboard RRHH API - Módulo de Partes de Horas y Auth Activo',
            'docs': 'Accede a /api/doc para la documentación interactiva',
            'endpoints': {
                'auth': '/api/login',
                'partes': '/api/partes',
                'mis_partes': '/api/mis-partes',
            },
        }
    )


# Respuestas JSON homogéneas cuando falta el token o no es válido
@jwt.unauthorized_loader
def sin_token(motivo):
    return jsonify({'message': 'Debes iniciar sesión.'}), 401


@jwt.invalid_token_loader
def token_invalido(motivo):
    return jsonify({'message': 'Sesión no válida. Vuelve a iniciar sesión.'}), 401


@jwt.expired_token_loader
def token_caducado(cabecera, payload):
    return jsonify({'message': 'La sesión ha caducado. Vuelve a iniciar sesión.'}), 401


def create_app(config_object=Config):
    """Crea la aplicación Flask con la configuración indicada (los tests usan otra BD)."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    CORS(
        app,
        resources={r'/api/*': {
            'origins': ['http://localhost:4200', 'http://127.0.0.1:4200'],
        }},
    )

    # Inicializar extensiones
    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)

    # La ruta '/' se registra ANTES de crear el Api: Flask-RESTX añade su propia
    # ruta '/' (endpoint 'root', que responde 404) y la primera registrada gana.
    app.add_url_rule('/', 'index', index)

    # Crear API con Swagger (Flask-RESTX)
    api = Api(
        app,
        version='2.0',
        title='Dashboard RRHH API',
        description='API para gestión de partes de horas, trabajadores, autenticación y reportes RRHH',
        doc='/api/doc',
        authorizations={
            'Bearer': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': 'Escribe: Bearer <token devuelto por /api/login>',
            },
        },
    )

    # Autenticación (mismas URLs que usa Angular: /api/login, /api/get-roles, /api/me)
    api.add_namespace(auth_ns, path='/api')
    # Partes de horas, horas extra, SP y plantilla
    api.add_namespace(partes_ns, path='/api/partes')
    # Partes de trabajo del propio empleado (formulario de alta y "Mis partes")
    api.add_namespace(mis_partes_ns, path='/api/mis-partes')

    return app


app = create_app()


if __name__ == '__main__':
    # Solo en local. El modo debug se activa con FLASK_DEBUG=1 en .env;
    # nunca exponerlo en red porque el depurador permite ejecutar código.
    app.run(host='127.0.0.1', port=5000, debug=os.getenv('FLASK_DEBUG') == '1')

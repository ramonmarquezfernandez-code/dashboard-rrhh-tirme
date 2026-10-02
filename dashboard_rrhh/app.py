from config import Config
from extensions import db, ma
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api

# Importar Blueprints y Namespaces
from routes.partes import partes_bp
from routes.api_v2 import partes_ns
from routes.auth_v2 import auth_ns

app = Flask(__name__)
app.config.from_object(Config)
CORS(
    app,
    resources={r'/api/*': {
        'origins': ['http://localhost:4200', 'http://127.0.0.1:4200'],
    }},
)

# Inicializar extensiones
db.init_app(app)
ma.init_app(app)

# Crear API con Swagger (Flask-RESTX)
api = Api(
    app,
    version='2.0',
    title='Dashboard RRHH API',
    description='API para gestión de partes de horas, trabajadores, autenticación y reportes RRHH',
    doc='/api/doc',
)

# Registrar namespaces de la API v2 con Swagger
api.add_namespace(auth_ns, path='/api/v2/auth')
api.add_namespace(partes_ns, path='/api/v2/partes')

# Registrar Blueprints legados (v1) si existen
try:
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)
except ImportError:
    pass

app.register_blueprint(partes_bp)


@app.route('/')
def index():
    return jsonify(
        {
            'status': 'online',
            'message': 'Dashboard RRHH API - Módulo de Partes de Horas y Auth Activo',
            'docs': 'Accede a /api/doc para la documentación interactiva',
            'endpoints': {
                'api_v1': '/api/partes',
                'api_v2_auth': '/api/v2/auth',
                'api_v2_partes': '/api/v2/partes',
            },
        }
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
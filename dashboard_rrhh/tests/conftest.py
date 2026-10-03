"""Fixtures compartidas. Los tests de login y acceso usan la BD epartes_test
del contenedor MariaDB (docker compose up -d); si no está disponible se saltan."""
import os

import pytest
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError

from app import create_app
from config import Config
from extensions import db
from seed import PASSWORD_PRUEBA, cargar_datos_prueba


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = URL.create(
        drivername='mysql+pymysql',
        username=Config.DB_USER,
        password=Config.DB_PASSWORD,
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        database=os.getenv('TEST_DB_NAME', 'epartes_test'),
        query={'charset': 'utf8mb4'},
    )


@pytest.fixture(scope='session')
def app_bd():
    """App conectada a epartes_test con tablas recién creadas y datos de prueba."""
    app = create_app(TestConfig)
    with app.app_context():
        try:
            db.drop_all()
        except OperationalError as error:
            pytest.skip(
                'MariaDB de tests no disponible (ejecuta "docker compose up -d" en la raíz '
                f'y, si el volumen es anterior, "docker compose down -v" antes): {error.orig}'
            )
        db.create_all()
        cargar_datos_prueba(db.session)
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client_bd(app_bd):
    return app_bd.test_client()


@pytest.fixture
def login(client_bd):
    """login(email, rol=None) -> respuesta de /api/login."""
    def _login(email, rol=None, password=PASSWORD_PRUEBA):
        datos = {'email': email, 'password': password}
        if rol:
            datos['rol'] = rol
        return client_bd.post('/api/login', json=datos)
    return _login


@pytest.fixture
def cabeceras(login):
    """cabeceras(email, rol) -> {'Authorization': 'Bearer <token>'} de un login válido."""
    def _cabeceras(email, rol=None):
        respuesta = login(email, rol)
        assert respuesta.status_code == 200, respuesta.get_json()
        return {'Authorization': f"Bearer {respuesta.get_json()['token']}"}
    return _cabeceras

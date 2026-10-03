"""Tests de humo: comprueban que la aplicación arranca y expone sus rutas
principales. No necesitan base de datos."""
import pytest

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


def test_index_responde_online(client):
    respuesta = client.get('/')
    assert respuesta.status_code == 200
    assert respuesta.get_json()['status'] == 'online'


def test_swagger_disponible(client):
    respuesta = client.get('/api/doc')
    assert respuesta.status_code == 200


def test_especificacion_openapi_incluye_namespaces(client):
    respuesta = client.get('/swagger.json')
    assert respuesta.status_code == 200
    rutas = respuesta.get_json()['paths']
    assert '/api/partes/he-por-periodo' in rutas
    assert not any(ruta.startswith('/api/v2') for ruta in rutas)
    assert '/api/login' in rutas
    assert '/api/me' in rutas


def test_rutas_del_frontend_registradas():
    """Rutas que usa el frontend Angular: auth y partes."""
    rutas = {regla.rule for regla in flask_app.url_map.iter_rules()}
    assert '/api/login' in rutas
    assert '/api/get-roles' in rutas
    assert '/api/partes/estados' in rutas

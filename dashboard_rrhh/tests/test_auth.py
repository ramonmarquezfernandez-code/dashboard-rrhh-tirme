"""Login con bcrypt + JWT, roles de get-roles y protección de endpoints."""
from flask_jwt_extended import decode_token

from extensions import db
from models import UserPayroll
from seed import PASSWORD_PRUEBA

MENSAJE_CREDENCIALES = 'Correo o contraseña incorrectos.'


def test_login_correcto_devuelve_jwt_con_claims(app_bd, login):
    respuesta = login('mgarcia@empresa.local', 'mando')
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos['user']['rolActivo'] == 'mando'
    assert datos['user']['roles'] == ['mando', 'empleado']

    with app_bd.app_context():
        claims = decode_token(datos['token'])
    assert claims['sub'] == '00000002'
    assert claims['email'] == 'mgarcia@empresa.local'
    assert claims['rol_activo'] == 'mando'
    assert claims['codgrs'] == [1]


def test_login_sin_rol_usa_el_de_mayor_prioridad(login):
    respuesta = login('eruiz@empresa.local')
    assert respuesta.status_code == 200
    assert respuesta.get_json()['user']['rolActivo'] == 'hr'


def test_email_sin_distinguir_mayusculas(login):
    assert login('JPerez@Empresa.Local').status_code == 200


def test_password_incorrecta(login):
    respuesta = login('jperez@empresa.local', password='otra')
    assert respuesta.status_code == 401
    assert respuesta.get_json()['message'] == MENSAJE_CREDENCIALES


def test_correo_inexistente_da_el_mismo_error(login):
    respuesta = login('nadie@empresa.local')
    assert respuesta.status_code == 401
    assert respuesta.get_json()['message'] == MENSAJE_CREDENCIALES


def test_puerta_trasera_admin_eliminada(login):
    assert login('admin@admin.org', password='').status_code == 401


def test_password_en_texto_plano_no_sirve(app_bd, client_bd):
    """Si en BD hubiera una contraseña sin hashear, no debe aceptarse."""
    with app_bd.app_context():
        usuario = db.session.scalar(db.select(UserPayroll).where(UserPayroll.NUMPER == '00000001'))
        hash_original = usuario.PASSWORD
        usuario.PASSWORD = PASSWORD_PRUEBA
        db.session.commit()
        try:
            respuesta = client_bd.post('/api/login', json={
                'email': 'jperez@empresa.local', 'password': PASSWORD_PRUEBA,
            })
            assert respuesta.status_code == 401
        finally:
            usuario.PASSWORD = hash_original
            db.session.commit()


def test_rol_no_permitido(login):
    # Un empleado sin roles en zgrroles intenta entrar como HR o como mando
    assert login('jperez@empresa.local', 'hr').status_code == 403
    assert login('jperez@empresa.local', 'mando').status_code == 403
    # Un mando no puede elegir HR
    assert login('mgarcia@empresa.local', 'hr').status_code == 403


def test_get_roles_reales(client_bd):
    esperados = {
        'jperez@empresa.local': ['empleado'],
        'mgarcia@empresa.local': ['mando', 'empleado'],
        'crodriguez@empresa.local': ['mando', 'empleado'],
        'atorres@empresa.local': ['hr', 'empleado'],
        'eruiz@empresa.local': ['hr', 'mando', 'empleado'],
    }
    for email, roles in esperados.items():
        respuesta = client_bd.post('/api/get-roles', json={'email': email, 'password': PASSWORD_PRUEBA})
        assert respuesta.status_code == 200
        assert respuesta.get_json()['roles'] == roles


def test_get_roles_no_revela_si_el_correo_existe(client_bd):
    """Sin contraseña válida, un correo existente y uno inexistente responden igual."""
    casos = [
        {'email': 'eruiz@empresa.local'},                          # sin contraseña
        {'email': 'eruiz@empresa.local', 'password': 'otra'},      # contraseña errónea
        {'email': 'nadie@empresa.local', 'password': 'otra'},      # correo inexistente
    ]
    for datos in casos:
        respuesta = client_bd.post('/api/get-roles', json=datos)
        assert respuesta.status_code == 401, datos
        assert respuesta.get_json()['message'] == MENSAJE_CREDENCIALES
        assert 'roles' not in respuesta.get_json()


def test_me_devuelve_la_sesion(client_bd, cabeceras):
    respuesta = client_bd.get('/api/me', headers=cabeceras('eruiz@empresa.local', 'mando'))
    assert respuesta.status_code == 200
    usuario = respuesta.get_json()['user']
    assert usuario['pernr'] == '00000005'
    assert usuario['rolActivo'] == 'mando'
    assert usuario['codgrs'] == [2]


def test_sin_token_401(client_bd):
    for url in ['/api/partes', '/api/partes/estados', '/api/partes/he-por-periodo',
                '/api/partes/plantilla-resumen', '/api/partes/ranking-combo', '/api/me']:
        assert client_bd.get(url).status_code == 401, url


def test_token_manipulado_401(client_bd, cabeceras):
    token = cabeceras('jperez@empresa.local')['Authorization']
    cabecera, payload, firma = token.split('.')
    manipulado = f'{cabecera}.{payload}.{firma[:-4]}AAAA'
    assert client_bd.get('/api/partes', headers={'Authorization': manipulado}).status_code == 401


def test_empleado_sin_acceso_a_pantallas_de_mando(client_bd, cabeceras):
    empleado = cabeceras('jperez@empresa.local')
    assert client_bd.get('/api/partes/ranking-combo', headers=empleado).status_code == 403
    assert client_bd.get('/api/partes/plantilla-resumen', headers=empleado).status_code == 403

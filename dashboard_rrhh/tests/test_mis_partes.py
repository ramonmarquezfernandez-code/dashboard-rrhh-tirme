"""Formulario de parte: /api/mis-partes contra la BD de tests.

La fixture crea dos periodos de nómina: uno abierto que incluye hoy y otro ya
traspasado, y al terminar borra los partes creados y los periodos.
"""
from datetime import date, timedelta

import pytest

from extensions import db
from models import ZParte, ZPeriodos

HOY = date.today()
AYER = HOY - timedelta(days=1)
EJERCICIO = str(HOY.year)


@pytest.fixture(scope='module')
def periodos(app_bd):
    with app_bd.app_context():
        filas = [
            ZPeriodos(ID='97', EJERCICIO=EJERCICIO, DESCRIPTION='Periodo abierto de prueba',
                      FECHAINI=HOY - timedelta(days=40), FECHAFIN=HOY + timedelta(days=5), TRASPASO=''),
            ZPeriodos(ID='96', EJERCICIO=EJERCICIO, DESCRIPTION='Periodo traspasado de prueba',
                      FECHAINI=HOY - timedelta(days=80), FECHAFIN=HOY - timedelta(days=41), TRASPASO='S'),
        ]
        db.session.add_all(filas)
        db.session.commit()
    # Fuera del contexto durante los tests: cada petición usa su propia sesión
    yield
    with app_bd.app_context():
        db.session.execute(db.delete(ZParte).where(ZParte.MES.in_(['96', '97'])))
        db.session.execute(db.delete(ZPeriodos).where(ZPeriodos.ID.in_(['96', '97']),
                                                      ZPeriodos.EJERCICIO == EJERCICIO))
        db.session.commit()


@pytest.fixture
def api(client_bd, cabeceras, periodos):
    """api(metodo, ruta, email, datos=None) -> respuesta."""
    def _api(metodo, ruta, email='jperez@empresa.local', datos=None, rol=None):
        return client_bd.open(f'/api/mis-partes{ruta}', method=metodo, json=datos, headers=cabeceras(email, rol))
    return _api


def parte(**cambios):
    datos = {
        'fecha': AYER.isoformat(), 'turno': 'M', 'entrada': '07:00', 'salida': '18:00', 'pausa': '00:00',
        'horas': {'normales': {'DL': 3}, 'llamadas': {'DL': 2}},
        'motivos': {'normales': 'Avería en la planta', 'llamadas': 'Guardia'},
        'situacion': 'teletrabajo', 'marcas': ['SP'], 'observaciones': 'Prueba',
    }
    datos.update(cambios)
    return datos


def fila(mandt):
    db.session.expire_all()
    return db.session.scalar(db.select(ZParte).where(ZParte.MANDT == mandt))


def test_configuracion(api):
    datos = api('GET', '/configuracion').get_json()
    assert [b['clave'] for b in datos['bloques']][:2] == ['normales', 'compensar']
    assert datos['limites']['max_total_he'] == 24
    assert {'clave': 'SP', 'etiqueta': 'Superior categoría'} in datos['marcas']


def test_crear_calcula_los_campos_del_servidor(app_bd, api):
    respuesta = api('POST', '', datos=parte(pernr='00000003', turno='T'))   # el PERNR del cuerpo se ignora
    assert respuesta.status_code == 201, respuesta.get_json()
    creado = respuesta.get_json()
    assert creado['estado'] == 'B' and creado['editable']
    assert creado['presencia_minutos'] == 11 * 60
    assert creado['total_he'] == 3

    with app_bd.app_context():
        guardado = fila(creado['mandt'])
        assert guardado.PERNR == '00000001'                # sale del token
        assert (guardado.MES, guardado.EJERC) == ('97', EJERCICIO)   # periodo de zperiodos
        assert guardado.TIPO == 'T' and guardado.STAT == 'B'
        assert guardado.HNDEC == '110000' and guardado.HN == 11
        assert guardado.DL == 3 and guardado.LLDL == 2 and guardado.DLC == 0
        assert guardado.MOTIVOHE == 'Avería en la planta' and guardado.MOTIVOLLA == 'Guardia'
        assert guardado.MOTIVOHEC is None
        assert (guardado.TELETRABAJO, guardado.ART21DESC, guardado.DESCANSO) == ('t', 'f', 'f')
        assert guardado.SP == 'X' and guardado.SUST is None
        assert guardado.CODGR == 1 and guardado.DPTO == 'Sistemas e IT'
        assert guardado.PERNRCR == '00000001' and guardado.CRDAT == HOY


def test_errores_de_validacion(api):
    respuesta = api('POST', '', datos=parte(
        turno='N', horas={'normales': {'DL': 20}, 'compensar': {'DL': 5}}, motivos={'normales': 'x'},
        entrada='00:00', salida='00:00'))
    assert respuesta.status_code == 400
    errores = respuesta.get_json()['errores']
    assert 'supera el máximo de 24' in errores['total_he']
    assert 'motivos.compensar' in errores


def test_duplicado_mismo_dia_y_turno(api):
    assert api('POST', '', datos=parte(turno='D')).status_code == 201
    respuesta = api('POST', '', datos=parte(turno='D'))
    assert respuesta.status_code == 400
    assert 'Ya tienes un parte' in respuesta.get_json()['errores']['turno']


def test_periodo_traspasado_y_fecha_futura(api):
    traspasado = api('POST', '', datos=parte(fecha=(HOY - timedelta(days=50)).isoformat()))
    assert 'traspasado' in traspasado.get_json()['errores']['fecha']
    futuro = api('POST', '', datos=parte(fecha=(HOY + timedelta(days=1)).isoformat()))
    assert 'futuros' in futuro.get_json()['errores']['fecha']


def test_listar_solo_los_propios(api):
    api('POST', '', email='mgarcia@empresa.local', rol='mando', datos=parte(turno='M'))
    propios = api('GET', f'?anio={EJERCICIO}').get_json()['partes']
    ajenos = api('GET', f'?anio={EJERCICIO}', email='mgarcia@empresa.local', rol='mando').get_json()['partes']
    assert propios and ajenos
    assert {p['mandt'] for p in propios}.isdisjoint({p['mandt'] for p in ajenos})
    # Solo los partes aún sin visto bueno (estado B) se pueden modificar
    assert all(p['editable'] == (p['estado']['valor'] == 'B') for p in propios)
    assert any(p['editable'] for p in propios)


def test_no_se_ve_ni_se_toca_el_parte_de_otro(api):
    ajeno = api('POST', '', email='crodriguez@empresa.local', rol='empleado', datos=parte(turno='M')).get_json()
    assert api('GET', f'/{ajeno["mandt"]}').status_code == 404
    assert api('PUT', f'/{ajeno["mandt"]}', datos=parte(turno='M')).status_code == 404
    assert api('DELETE', f'/{ajeno["mandt"]}').status_code == 404


def test_editar_y_borrar_en_estado_b(api):
    creado = api('POST', '', datos=parte(fecha=(HOY - timedelta(days=2)).isoformat(), turno='M')).get_json()
    # Sin reintroducir entrada/salida se conserva la presencia guardada (11 h)
    cambios = parte(fecha=creado['fecha'], turno='M', entrada='', salida='',
                    horas={'compensar': {'DL': 2}}, motivos={'compensar': 'Refuerzo'}, situacion='ninguna')
    editado = api('PUT', f'/{creado["mandt"]}', datos=cambios)
    assert editado.status_code == 200, editado.get_json()
    assert editado.get_json()['horas']['compensar']['DL'] == 2
    assert editado.get_json()['horas']['normales']['DL'] == 0
    assert editado.get_json()['presencia_minutos'] == 11 * 60
    assert api('DELETE', f'/{creado["mandt"]}').status_code == 204
    assert api('GET', f'/{creado["mandt"]}').status_code == 404


def test_parte_validado_no_se_puede_modificar(app_bd, api):
    creado = api('POST', '', datos=parte(fecha=(HOY - timedelta(days=3)).isoformat())).get_json()
    with app_bd.app_context():
        fila(creado['mandt']).STAT = 'C'       # visto bueno del jefe de área
        db.session.commit()
    assert api('GET', f'/{creado["mandt"]}').get_json()['editable'] is False
    assert api('PUT', f'/{creado["mandt"]}', datos=parte(fecha=creado['fecha'])).status_code == 409
    assert api('DELETE', f'/{creado["mandt"]}').status_code == 409


def test_el_parte_aparece_en_el_dashboard(client_bd, cabeceras, api):
    fecha = HOY - timedelta(days=4)
    api('POST', '', datos=parte(fecha=fecha.isoformat(), turno='N', horas={'normales': {'DL': 5}}))
    respuesta = client_bd.get('/api/partes/he-por-empleado', headers=cabeceras('jperez@empresa.local'),
                              query_string={'anio': fecha.year, 'anio_natural': 'true',
                                            'mes_desde': fecha.month, 'mes_hasta': fecha.month})
    horas = {e['pernr']: e['horas_extra'] for e in respuesta.get_json()['empleados']}
    assert horas.get('00000001', 0) >= 5


def test_sin_token(client_bd, periodos):
    assert client_bd.get('/api/mis-partes').status_code == 401
    assert client_bd.post('/api/mis-partes', json=parte()).status_code == 401

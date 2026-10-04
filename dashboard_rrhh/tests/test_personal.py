"""Directorio de personal y ejercicios disponibles, filtrados por perfil.

Plantilla del seed: grupo 1 (Grupo Técnico A, área Desarrollo Software) =
00000001, 00000002, 00000004; grupo 2 (Grupo Operativo B, área Mantenimiento
y Planta) = 00000003, 00000005. Partes del seed: ejercicio 2026.
"""
from datetime import date

import pytest

CLAVES_EMPLEADO = {'pernr', 'nombre', 'apellidos', 'email', 'grupo', 'area', 'departamento'}
GRUPO_1, GRUPO_2 = 'Grupo Técnico A', 'Grupo Operativo B'


def personal(client_bd, cabeceras, email, rol, **params):
    return client_bd.get('/api/partes/personal', query_string=params, headers=cabeceras(email, rol))


@pytest.mark.parametrize('email, rol, pernrs', [
    ('atorres@empresa.local', 'hr', {'00000001', '00000002', '00000003', '00000004', '00000005'}),
    ('mgarcia@empresa.local', 'mando', {'00000001', '00000002', '00000004'}),
    ('crodriguez@empresa.local', 'mando', {'00000003', '00000005'}),
])
def test_personal_filtrado_por_perfil(client_bd, cabeceras, email, rol, pernrs):
    datos = personal(client_bd, cabeceras, email, rol).get_json()
    assert {e['pernr'] for e in datos['empleados']} == pernrs
    assert datos['total'] == len(pernrs)


def test_empleado_no_ve_el_directorio(client_bd, cabeceras):
    assert personal(client_bd, cabeceras, 'jperez@empresa.local', None).status_code == 403


def test_personal_no_expone_datos_sensibles(client_bd, cabeceras):
    datos = personal(client_bd, cabeceras, 'atorres@empresa.local', 'hr').get_json()
    for empleado in datos['empleados']:
        assert set(empleado) == CLAVES_EMPLEADO


def test_personal_contenido_y_orden(client_bd, cabeceras):
    empleados = personal(client_bd, cabeceras, 'atorres@empresa.local', 'hr').get_json()['empleados']
    juan = next(e for e in empleados if e['pernr'] == '00000001')
    assert juan == {
        'pernr': '00000001', 'nombre': 'Juan', 'apellidos': 'Pérez Gómez',
        'email': 'jperez@empresa.local', 'grupo': GRUPO_1,
        'area': 'Desarrollo Software', 'departamento': 'Sistemas e IT',
    }
    apellidos = [e['apellidos'] for e in empleados]
    assert apellidos == sorted(apellidos)


def test_personal_filtros_y_opciones(client_bd, cabeceras):
    hr = personal(client_bd, cabeceras, 'atorres@empresa.local', 'hr', grupo=GRUPO_2).get_json()
    assert {e['pernr'] for e in hr['empleados']} == {'00000003', '00000005'}
    # Las opciones de los combos no dependen del filtro aplicado
    assert hr['grupos'] == [GRUPO_2, GRUPO_1]
    assert hr['areas'] == ['Desarrollo Software', 'Mantenimiento y Planta']

    por_area = personal(client_bd, cabeceras, 'atorres@empresa.local', 'hr', direccion='Desarrollo Software')
    assert por_area.get_json()['total'] == 3
    todos = personal(client_bd, cabeceras, 'atorres@empresa.local', 'hr', grupo='TODOS', direccion='TODAS')
    assert todos.get_json()['total'] == 5

    mando = personal(client_bd, cabeceras, 'crodriguez@empresa.local', 'mando').get_json()
    assert mando['grupos'] == [GRUPO_2]


def test_plantilla_resumen_incluye_opciones(client_bd, cabeceras):
    datos = client_bd.get('/api/partes/plantilla-resumen', headers=cabeceras('mgarcia@empresa.local', 'mando')).get_json()
    assert datos['grupos'] == [GRUPO_1]
    assert datos['areas'] == ['Desarrollo Software']


@pytest.mark.parametrize('email, rol', [
    ('atorres@empresa.local', 'hr'),
    ('jperez@empresa.local', 'empleado'),
])
def test_ejercicios(client_bd, cabeceras, email, rol):
    datos = client_bd.get('/api/partes/ejercicios', headers=cabeceras(email, rol)).get_json()
    actual = str(date.today().year)
    assert datos['ejercicios'] == sorted({'2026', actual}, reverse=True)
    # Los partes visibles son de 2026: es el actual tanto si es el año en curso como si no
    assert datos['actual'] == '2026'


def test_ejercicios_sin_partes_visibles(app_bd):
    """Sin datos, el único ejercicio es el año en curso."""
    from sqlalchemy import false

    from services.horas_extra_service import HorasExtraService

    with app_bd.app_context():
        datos = HorasExtraService(false()).ejercicios(hoy=date(2031, 5, 1))
    assert datos == {'ejercicios': ['2031'], 'actual': '2031'}


def test_ejercicios_con_anio_en_curso_sin_datos(app_bd):
    from sqlalchemy import true

    from services.horas_extra_service import HorasExtraService

    with app_bd.app_context():
        datos = HorasExtraService(true()).ejercicios(hoy=date(2031, 5, 1))
    assert datos['ejercicios'][0] == '2031'
    assert datos['actual'] == '2026'  # el más reciente con partes

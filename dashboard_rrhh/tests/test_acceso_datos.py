"""Aislamiento de datos por rol (filtro aplicado en el backend).

Partes de prueba (ver seed.py):
    00000001 (Juan)   grupo 1, 2 partes
    00000003 (Carlos) grupo 2, 1 parte
    00000002 (María)  grupo 2, 1 parte (es VB del grupo 1)
Plantilla activa: grupo 1 = 00000001, 00000002, 00000004; grupo 2 = 00000003, 00000005.
"""
import pytest

# (email, rol, PERNR de los partes visibles con repeticiones, total de plantilla visible)
CASOS = [
    ('atorres@empresa.local', 'hr', ['00000001', '00000001', '00000002', '00000003'], 5),
    ('mgarcia@empresa.local', 'mando', ['00000001', '00000001', '00000002'], 3),
    ('crodriguez@empresa.local', 'mando', ['00000002', '00000003'], 2),
    ('jperez@empresa.local', 'empleado', ['00000001', '00000001'], None),
    ('eruiz@empresa.local', 'hr', ['00000001', '00000001', '00000002', '00000003'], 5),
    ('eruiz@empresa.local', 'mando', ['00000002', '00000003'], 2),
    ('mgarcia@empresa.local', 'empleado', ['00000002'], None),
]
IDS = [f"{email.split('@')[0]}-{rol}" for email, rol, _, _ in CASOS]


@pytest.mark.parametrize('email, rol, pernrs, plantilla', CASOS, ids=IDS)
def test_listado_de_partes(client_bd, cabeceras, email, rol, pernrs, plantilla):
    datos = client_bd.get('/api/partes?per_page=100', headers=cabeceras(email, rol)).get_json()
    assert sorted(p['PERNR'] for p in datos['partes']) == pernrs
    assert datos['total'] == len(pernrs)


@pytest.mark.parametrize('email, rol, pernrs, plantilla', CASOS, ids=IDS)
def test_he_por_empleado(client_bd, cabeceras, email, rol, pernrs, plantilla):
    datos = client_bd.get('/api/partes/he-por-empleado?anio=2026', headers=cabeceras(email, rol)).get_json()
    assert sorted(e['pernr'] for e in datos['empleados']) == sorted(set(pernrs))


@pytest.mark.parametrize('email, rol, pernrs, plantilla', CASOS, ids=IDS)
def test_he_por_periodo(client_bd, cabeceras, email, rol, pernrs, plantilla):
    datos = client_bd.get('/api/partes/he-por-periodo?anio=2026', headers=cabeceras(email, rol)).get_json()
    assert sorted(t['id'] for t in datos['trabajadores']) == sorted(set(pernrs))


@pytest.mark.parametrize('email, rol, pernrs, plantilla', CASOS, ids=IDS)
def test_plantilla_resumen(client_bd, cabeceras, email, rol, pernrs, plantilla):
    respuesta = client_bd.get('/api/partes/plantilla-resumen', headers=cabeceras(email, rol))
    if plantilla is None:
        assert respuesta.status_code == 403  # los empleados no ven la plantilla
    else:
        assert respuesta.status_code == 200
        assert respuesta.get_json()['total_plantilla'] == plantilla


def test_partes_de_otro_empleado_no_visibles(client_bd, cabeceras):
    empleado = cabeceras('jperez@empresa.local')
    assert client_bd.get('/api/partes/empleado/00000001', headers=empleado).status_code == 200
    assert client_bd.get('/api/partes/empleado/00000003', headers=empleado).status_code == 404


def test_mando_ve_su_grupo_pero_no_otros(client_bd, cabeceras):
    vb_grupo_1 = cabeceras('mgarcia@empresa.local', 'mando')
    assert client_bd.get('/api/partes/empleado/00000001', headers=vb_grupo_1).status_code == 200
    assert client_bd.get('/api/partes/empleado/00000003', headers=vb_grupo_1).status_code == 404


def test_pernr_en_filtro_no_salta_el_control(client_bd, cabeceras):
    """Pedir explícitamente el PERNR de otro no devuelve sus datos."""
    empleado = cabeceras('jperez@empresa.local')
    url = '/api/partes/he-por-empleado?anio=2026&pernr=00000003'
    assert client_bd.get(url, headers=empleado).get_json()['empleados'] == []


@pytest.mark.parametrize('url, clave_pernr', [
    ('/api/partes/resumen-trabajador?anio=2026', 'id'),
    ('/api/partes/comite?anio=2026', 'id_empleado'),
    ('/api/partes/he-anio-natural?anio=2026', 'id'),
])
def test_resumenes_por_trabajador_filtrados(client_bd, cabeceras, url, clave_pernr):
    datos = client_bd.get(url, headers=cabeceras('jperez@empresa.local')).get_json()
    assert {fila[clave_pernr] for fila in datos} == {'00000001'}

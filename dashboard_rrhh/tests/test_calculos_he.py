"""Cálculos de horas extra contra la BD de tests, con valores conocidos.

Los partes se crean en el ejercicio 2030 (no coincide con los datos del seed,
que son de 2026) y se borran al terminar el módulo. Se consulta como HR para
que el filtro de perfil no intervenga: el aislamiento ya lo prueba
test_acceso_datos.py.

Valores de cada parte (columnas a 0 si no se indican):

  P1  00000001  PADAT 2030-03-10  MES 03  Sistemas e IT  estado A  SP 't'
      DL=1 DF=2 NL=3 NF=4 (normales 10)  DLC=1 DFC=1 (compensar 2)  DLB=3 (busca 3)
      DLBN=4 (buscaNP 4)  DLCO=5 (combo 5)  DLF=6 (F)  DLCOP=7 (combo programadas)
      total periodo = 10+2+3+4+5 = 24      total ranking = 24+6+7 = 37
      compensables = 10   convertidas = 1*1.6 + 2*2 + 3*2 + 4*2.5 = 21.6
  P2  00000001  PADAT 2030-04-02  MES 03  Sistemas e IT  estado B  SP 'X'
      NL=2 (normales 2)  DLB=1 (busca 1)            total 3, convertidas 4.0
  P3  00000003  PADAT 2030-03-15  MES 03  Operaciones    estado A  SP 'f'
      NFC=1 (compensar 1)  DFCO=10 (combo 10)       total 11, compensables 0
  P4  00000003  PADAT 2030-05-20  MES 05  Operaciones    estado A  SP '0'
      DL=4 (normales 4)                             total 4, convertidas 6.4

P2 pertenece al periodo de marzo (MES 03) pero su fecha es de abril: cuenta en
marzo al consultar por periodo y en abril al consultar por año natural.
"""
from datetime import date

import pytest

from extensions import db
from models import EppartStatus, ZParte, ZPeriodos

ANIO = '2030'
PARTES = [
    dict(MANDT=9000000000001, PERNR='00000001', PADAT=date(2030, 3, 10), MES='03', CODGR=1,
         DPTO='Sistemas e IT', STAT='A', SP='t', DL=1, DF=2, NL=3, NF=4, DLC=1, DFC=1,
         DLB=3, DLBN=4, DLCO=5, DLF=6, DLCOP=7),
    dict(MANDT=9000000000002, PERNR='00000001', PADAT=date(2030, 4, 2), MES='03', CODGR=1,
         DPTO='Sistemas e IT', STAT='B', SP='X', NL=2, DLB=1),
    dict(MANDT=9000000000003, PERNR='00000003', PADAT=date(2030, 3, 15), MES='03', CODGR=2,
         DPTO='Operaciones', STAT='A', SP='f', NFC=1, DFCO=10),
    dict(MANDT=9000000000004, PERNR='00000003', PADAT=date(2030, 5, 20), MES='05', CODGR=2,
         DPTO='Operaciones', STAT='A', SP='0', DL=4),
]
CERO = {'normales': 0, 'compensar': 0, 'busca': 0, 'buscanp': 0, 'combo': 0, 'total': 0}


@pytest.fixture(scope='module')
def datos_he(app_bd):
    with app_bd.app_context():
        estados_nuevos = []
        for codigo in ('A', 'B'):
            if db.session.get(EppartStatus, codigo) is None:
                db.session.add(EppartStatus(STATUS=codigo, DESCRIPTION=f'Estado {codigo}', COLOR='#000000'))
                estados_nuevos.append(codigo)
        db.session.flush()
        db.session.add(ZPeriodos(ID='03', EJERCICIO=ANIO, DESCRIPTION='Marzo 2030',
                                 FECHAINI=date(2030, 3, 1), FECHAFIN=date(2030, 3, 31)))
        for parte in PARTES:
            db.session.add(ZParte(TIPO='N', TURNO='M', EJERC=ANIO, **parte))
        db.session.commit()
    # Fuera del contexto durante los tests: cada petición usa su propia sesión
    yield
    with app_bd.app_context():
        db.session.execute(db.delete(ZParte).where(ZParte.EJERC == ANIO))
        db.session.execute(db.delete(ZPeriodos).where(ZPeriodos.EJERCICIO == ANIO))
        if estados_nuevos:
            db.session.execute(db.delete(EppartStatus).where(EppartStatus.STATUS.in_(estados_nuevos)))
        db.session.commit()


@pytest.fixture
def consultar(client_bd, cabeceras, datos_he):
    """consultar(endpoint, **params) -> JSON de /api/partes/<endpoint> como HR."""
    hr = cabeceras('atorres@empresa.local', 'hr')

    def _consultar(endpoint, **params):
        respuesta = client_bd.get(f'/api/partes/{endpoint}', query_string={'anio': ANIO, **params}, headers=hr)
        assert respuesta.status_code == 200, respuesta.get_json()
        return respuesta.get_json()
    return _consultar


def cifras(fila, claves=('normales', 'compensar', 'busca', 'buscanp', 'combo', 'total')):
    """Valores numéricos de una fila (acepta números o texto numérico)."""
    return {clave: int(fila[clave]) for clave in claves}


def por_clave(filas, clave):
    return {fila[clave]: fila for fila in filas}


# --- HE por periodo ----------------------------------------------------------

def test_he_por_periodo_desglose_mensual(consultar):
    mensual = {str(m['mes']).zfill(2): cifras(m) for m in consultar('he-por-periodo')['mensual']}
    assert list(mensual) == [f'{mes:02d}' for mes in range(1, 13)]
    assert mensual['03'] == {'normales': 12, 'compensar': 3, 'busca': 4, 'buscanp': 4, 'combo': 15, 'total': 38}
    assert mensual['05'] == {**CERO, 'normales': 4, 'total': 4}
    assert mensual['04'] == CERO


def test_he_por_periodo_por_departamento_y_trabajador(consultar):
    datos = consultar('he-por-periodo')
    departamentos = por_clave(datos['departamentos'], 'departamento')
    assert cifras(departamentos['Sistemas e IT']) == {'normales': 12, 'compensar': 2, 'busca': 4, 'buscanp': 4, 'combo': 5, 'total': 27}
    assert cifras(departamentos['Operaciones']) == {'normales': 4, 'compensar': 1, 'busca': 0, 'buscanp': 0, 'combo': 10, 'total': 15}
    # Ordenados por total descendente
    assert [d['departamento'] for d in datos['departamentos']] == ['Sistemas e IT', 'Operaciones']

    trabajadores = por_clave(datos['trabajadores'], 'id')
    assert int(trabajadores['00000001']['total']) == 27
    assert trabajadores['00000001']['nombre'] == 'Juan'
    assert trabajadores['00000001']['departamento'] == 'Sistemas e IT'
    assert int(trabajadores['00000003']['total']) == 15


def test_total_periodo_excluye_f_y_combo_programadas(consultar):
    """P1 tiene DLF=6 y DLCOP=7, que no cuentan en el total de HE por periodo."""
    trabajadores = por_clave(consultar('he-por-periodo', pernr='00000001', estado='A')['trabajadores'], 'id')
    assert int(trabajadores['00000001']['total']) == 24


def test_anio_natural_usa_la_fecha_y_periodo_usa_el_mes(consultar):
    natural = {str(m['mes']).zfill(2): cifras(m) for m in consultar('he-por-periodo', anio_natural='true')['mensual']}
    assert natural['03'] == {'normales': 10, 'compensar': 3, 'busca': 3, 'buscanp': 4, 'combo': 15, 'total': 35}
    assert natural['04'] == {**CERO, 'normales': 2, 'busca': 1, 'total': 3}


def test_rango_de_meses(consultar):
    datos = consultar('he-por-periodo', mes_desde=4, mes_hasta=5)
    assert [str(m['mes']).zfill(2) for m in datos['mensual']] == ['04', '05']
    assert {t['id']: int(t['total']) for t in datos['trabajadores']} == {'00000003': 4}


def test_periodo_seleccionado(consultar):
    datos = consultar('he-por-periodo', periodo_id='03')
    assert [m['mes'] for m in datos['mensual']] == ['03']
    assert int(datos['mensual'][0]['total']) == 38
    assert {t['id']: int(t['total']) for t in datos['trabajadores']} == {'00000001': 27, '00000003': 11}
    assert datos['periodos'] == [{
        'id': '03', 'ejercicio': '2030', 'descripcion': 'Marzo 2030',
        'fecha_inicio': '2030-03-01', 'fecha_fin': '2030-03-31',
    }]


@pytest.mark.parametrize('filtro, esperado', [
    ({'departamento': 'Operaciones'}, {'00000003': 15}),
    ({'estado': 'B'}, {'00000001': 3}),
    ({'pernr': '00000003'}, {'00000003': 15}),
    ({'departamento': 'No existe'}, {}),
])
def test_filtros(consultar, filtro, esperado):
    datos = consultar('he-por-periodo', **filtro)
    assert {t['id']: int(t['total']) for t in datos['trabajadores']} == esperado


def test_cifras_numericas_en_he_por_periodo(consultar):
    """Contrato del frontend (he.service.ts): las cifras son números, no texto."""
    datos = consultar('he-por-periodo')
    for fila in datos['mensual'] + datos['departamentos'] + datos['trabajadores']:
        for clave in CERO:
            assert isinstance(fila[clave], int), (clave, fila)
    assert all(isinstance(m['mes'], str) and len(m['mes']) == 2 for m in datos['mensual'])
    natural = consultar('he-por-periodo', anio_natural='true')['mensual']
    assert all(isinstance(m['mes'], str) and len(m['mes']) == 2 for m in natural)


# --- HE por empleado ---------------------------------------------------------

def test_he_por_empleado(consultar):
    datos = consultar('he-por-empleado')
    assert [(e['pernr'], e['horas_extra']) for e in datos['empleados']] == [('00000001', 27), ('00000003', 15)]
    assert datos['total'] == 42
    assert datos['departamentos'] == ['Operaciones', 'Sistemas e IT']
    assert datos['empleados'][0]['nombre'] == 'Juan'


def test_he_por_empleado_orden(consultar):
    # Año natural, abril-mayo: 00000001 suma 3 h (P2) y 00000003 suma 4 h (P4)
    params = {'anio_natural': 'true', 'mes_desde': 4, 'mes_hasta': 5}
    por_horas = consultar('he-por-empleado', orden='horas', **params)
    assert por_horas['orden'] == 'horas'
    assert [(e['pernr'], e['horas_extra']) for e in por_horas['empleados']] == [('00000003', 4), ('00000001', 3)]
    por_pernr = consultar('he-por-empleado', orden='pernr', **params)
    assert por_pernr['orden'] == 'pernr'
    assert [e['pernr'] for e in por_pernr['empleados']] == ['00000001', '00000003']


# --- Ranking combo -----------------------------------------------------------

def test_ranking_combo(consultar):
    datos = consultar('ranking-combo')
    filas = por_clave(datos['filas'], 'pernr')
    assert filas['00000001'] == {
        'pernr': '00000001', 'nombre': 'Juan', 'apellidos': 'Pérez Gómez',
        'combo_programadas': 7.0, 'total_he': 40.0,
        'he_compensables': 12.0, 'he_compensables_convertidas': 25.6,
    }
    assert filas['00000003']['total_he'] == 15.0
    assert filas['00000003']['he_compensables'] == 4.0
    assert filas['00000003']['he_compensables_convertidas'] == 6.4
    assert [f['pernr'] for f in datos['filas']] == ['00000001', '00000003']
    assert datos['totales'] == {
        'combo_programadas': 7.0, 'total_he': 55.0,
        'he_compensables': 16.0, 'he_compensables_convertidas': 32.0,
    }


def test_total_ranking_incluye_f_y_combo_programadas(consultar):
    filas = consultar('ranking-combo', pernr='00000001', estado='A')['filas']
    assert filas[0]['total_he'] == 37.0
    assert filas[0]['he_compensables_convertidas'] == 21.6


# --- Resúmenes por ejercicio ---------------------------------------------------

def test_resumen_departamento(consultar):
    filas = por_clave(consultar('resumen-departamento'), 'departamento')
    assert cifras(filas['Sistemas e IT'])['total'] == 27
    assert cifras(filas['Operaciones']) == {'normales': 4, 'compensar': 1, 'busca': 0, 'buscanp': 0, 'combo': 10, 'total': 15}


def test_resumen_trabajador_y_retribuible(consultar):
    filas = por_clave(consultar('resumen-trabajador'), 'id')
    assert int(filas['00000001']['total']) == 27
    assert int(filas['00000001']['totalretrib']) == 16  # normales 12 + busca 4
    assert int(filas['00000003']['totalretrib']) == 4
    assert filas['00000001']['trabajador'] == 'Juan'


def test_comite_y_anio_natural(consultar):
    assert {f['id_empleado']: int(f['horas_extras']) for f in consultar('comite')} == {'00000001': 27, '00000003': 15}
    filas = consultar('he-anio-natural')
    assert [(f['id'], int(f['total_he_anio'])) for f in filas] == [('00000001', 27), ('00000003', 15)]


# --- SP -----------------------------------------------------------------------

def test_sp_cuenta_solo_valores_marcados(consultar):
    """'t' y 'X' cuentan como SP; 'f', '0' y NULL no (ver VALORES_MARCADO)."""
    datos = consultar('sp-resumen-periodos', fecha_hasta='2030-12-31')
    doce = datos['periodos']['12']
    assert doce['fecha_desde'] == '2029-12-31'
    assert {p['id']: p['sp'] for p in doce['personas']} == {'00000001': 2}
    assert doce['total_sp'] == 2
    assert doce['total_personas'] == 1
    assert doce['departamentos'] == [{'departamento': 'Sistemas e IT', 'sp': 2}]

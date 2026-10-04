"""Generador de datos de demostración (generar_datos.py) sobre la BD de tests.

Genera unos 2.000 partes, comprueba su coherencia y, al terminar, deja la BD
con los datos del seed para que el resto de tests no se vea afectado.
"""
from datetime import date

import pytest

from extensions import db
from generar_datos import EMPLEADOS_TOTALES, GRUPOS, GeneradorDatos
from seed import USUARIOS, cargar_datos_prueba

HASTA = date(2026, 10, 3)
PARTES = 2_000


def consultar(conexion, sql, parametros=None):
    with conexion.cursor() as cursor:
        cursor.execute(sql, parametros)
        return cursor.fetchall()


@pytest.fixture(scope='module')
def generado(app_bd):
    with app_bd.app_context():
        conexion = db.engine.raw_connection()
    try:
        resumen = GeneradorDatos(conexion, partes=PARTES, semilla=7, hasta=HASTA).generar()
        conexion.commit()
        yield conexion, resumen
    finally:
        conexion.close()
        # Restaurar los datos del seed (el generador vacía partes, empleados, grupos...)
        with app_bd.app_context():
            with db.engine.begin() as transaccion:
                for tabla in ('zparte', 'zgrroles', 'userpayroll', 'zperiodos',
                              'grupospayroll', 'departmentspayroll', 'areaspayroll'):
                    transaccion.exec_driver_sql(f'DELETE FROM `{tabla}`')
            cargar_datos_prueba(db.session)


def test_resumen(generado):
    _, resumen = generado
    assert resumen.empleados == EMPLEADOS_TOTALES
    assert resumen.grupos == len(GRUPOS) == 25
    assert abs(resumen.partes - PARTES) < PARTES * 0.1
    assert set(resumen.partes_por_ejercicio) == {2024, 2025, 2026}
    # En la explotación real ~6 % de los partes tiene horas extra
    assert 0.03 < resumen.partes_con_he / resumen.partes < 0.12


def test_recuentos_en_bd(generado):
    conexion, resumen = generado
    assert consultar(conexion, 'SELECT COUNT(*) FROM userpayroll')[0][0] == EMPLEADOS_TOTALES
    assert consultar(conexion, 'SELECT COUNT(*) FROM grupospayroll')[0][0] == 25
    assert consultar(conexion, 'SELECT COUNT(*) FROM zparte')[0][0] == resumen.partes
    # Periodos de nómina de ene-2024 al periodo de la fecha final (10/2026)
    assert consultar(conexion, 'SELECT COUNT(*) FROM zperiodos')[0][0] == 34


def test_partes_coherentes_con_el_empleado(generado):
    conexion, _ = generado
    incoherentes = consultar(conexion, """
        SELECT COUNT(*) FROM zparte p
        JOIN userpayroll u ON u.NUMPER = p.PERNR
        JOIN departmentspayroll d ON d.CODE = u.DEPARTMENT
        WHERE p.CODGR <> u.GRUPO OR p.DPTO <> d.NAME
    """)[0][0]
    assert incoherentes == 0


def test_fechas_y_periodos(generado):
    conexion, _ = generado
    fila = consultar(conexion, """
        SELECT MIN(PADAT), MAX(PADAT), SUM(UPDAT > %s OR CRDAT < PADAT) FROM zparte
    """, (HASTA,))[0]
    assert fila[0] >= date(2024, 1, 1)
    assert fila[1] <= HASTA
    assert int(fila[2]) == 0
    # MES/EJERC es el periodo de nómina (del 11 al 10) que contiene la fecha del parte
    fuera_de_periodo = consultar(conexion, """
        SELECT COUNT(*) FROM zparte p LEFT JOIN zperiodos z
          ON z.ID = p.MES AND z.EJERCICIO = p.EJERC AND p.PADAT BETWEEN z.FECHAINI AND z.FECHAFIN
        WHERE z.ID IS NULL
    """)[0][0]
    assert fuera_de_periodo == 0
    # Como en la BD real, la mayoría de partes tiene un MES distinto del mes natural de la fecha
    distinto = consultar(conexion, "SELECT AVG(MES <> LPAD(MONTH(PADAT), 2, '0')) FROM zparte")[0][0]
    assert 0.5 < float(distinto) < 0.8


def test_estados_y_firmas(generado):
    conexion, _ = generado
    estados = {fila[0] for fila in consultar(conexion, 'SELECT DISTINCT STAT FROM zparte')}
    assert estados <= set('ABCDEFGHI')
    # Partes de meses cerrados: traspasados a nómina y con todas las firmas
    sin_firmas = consultar(conexion, """
        SELECT COUNT(*) FROM zparte
        WHERE STAT IN ('G', 'H', 'I') AND (PERNRVB IS NULL OR PERNRFI IS NULL OR PERNRHR IS NULL)
    """)[0][0]
    assert sin_firmas == 0
    # Periodos ya cerrados (hasta el 10/09/2026): traspasados o modificados por RRHH
    abiertos = consultar(conexion, "SELECT COUNT(*) FROM zparte WHERE PADAT < '2026-09-11' AND STAT NOT IN ('G', 'H', 'I')")
    assert abiertos[0][0] == 0
    assert {fila[0] for fila in consultar(conexion, 'SELECT DISTINCT TIPO FROM zparte')} == {'T'}


def test_horas_no_negativas(generado):
    conexion, _ = generado
    negativas = consultar(conexion, """
        SELECT COUNT(*) FROM zparte WHERE LEAST(DL, DF, NL, NF, DLB, DFB, NLB, NFB, DLC, DFC, NLC, NFC,
                                                 DLCO, DFCO, NLCO, NFCO, DLBN, DFBN, NLBN, NFBN) < 0
    """)[0][0]
    assert negativas == 0


def test_roles_como_en_produccion(generado):
    conexion, _ = generado
    # Todos los grupos tienen al menos un FI; VB solo en algunos (como en la tabla real)
    con_fi = consultar(conexion, "SELECT COUNT(DISTINCT CODGR) FROM zgrroles WHERE ROLNAME = 'FI'")[0][0]
    con_vb = consultar(conexion, "SELECT COUNT(DISTINCT CODGR) FROM zgrroles WHERE ROLNAME = 'VB'")[0][0]
    assert con_fi == 25
    assert 2 <= con_vb < 25
    assert consultar(conexion, "SELECT COUNT(DISTINCT PERNR) FROM zgrroles WHERE ROLNAME = 'HR'")[0][0] == 3
    # Nadie con rol está dado de baja
    inactivos_con_rol = consultar(conexion, """
        SELECT COUNT(*) FROM zgrroles r JOIN userpayroll u ON u.NUMPER = r.PERNR WHERE u.ACTIVE = 0
    """)[0][0]
    assert inactivos_con_rol == 0


def test_usuarios_de_prueba_conservados(generado):
    conexion, _ = generado
    for numper, nombre, _, email, grupo, _, _, roles in USUARIOS:
        fila = consultar(conexion, 'SELECT NAME, EMAIL, GRUPO FROM userpayroll WHERE NUMPER = %s', (numper,))[0]
        assert fila == (nombre, email, grupo)
        en_bd = set(consultar(conexion, 'SELECT ROLNAME, CODGR FROM zgrroles WHERE PERNR = %s', (numper,)))
        assert set(roles) <= en_bd


def test_misma_semilla_misma_huella(generado):
    conexion, resumen = generado
    repetido = GeneradorDatos(conexion, partes=PARTES, semilla=7, hasta=HASTA).generar()
    assert repetido.huella == resumen.huella
    assert repetido.partes == resumen.partes

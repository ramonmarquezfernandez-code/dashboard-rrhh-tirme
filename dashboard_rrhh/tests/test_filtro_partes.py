"""ParametrosConsulta y FiltroPartesBuilder (no necesitan base de datos)."""
from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import literal, true
from sqlalchemy.dialects import mysql
from werkzeug.datastructures import MultiDict

from models import ZParte
from services.filtro_partes import FiltroPartesBuilder, ParametroInvalido, ParametrosConsulta
from services.sp_service import marcado, restar_meses


def sql(condiciones):
    """Condiciones compiladas a SQL de MariaDB con los valores en línea."""
    return [str(c.compile(dialect=mysql.dialect(), compile_kwargs={'literal_binds': True})) for c in condiciones]


def params(**valores):
    return ParametrosConsulta.desde_args(MultiDict(valores))


# --- ParametrosConsulta ---------------------------------------------------------

def test_valores_por_defecto():
    p = params()
    assert (p.anio, p.mes_desde, p.mes_hasta, p.anio_natural, p.orden) == ('2026', 1, 12, False, 'horas')
    assert p.meses() == ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']


def test_lectura_y_limpieza():
    p = params(anio='2030', mes_desde='3', mes_hasta='5', anio_natural='SI', departamento='  Operaciones ',
               pernr='00000001', estado='A', periodo_id='03', orden='PERNR')
    assert p.meses() == ['03', '04', '05']
    assert p.anio_natural is True
    assert (p.departamento, p.pernr, p.estado, p.periodo_id, p.orden) == ('Operaciones', '00000001', 'A', '03', 'pernr')


def test_meses_fuera_de_rango_se_recortan():
    p = params(mes_desde='0', mes_hasta='15')
    assert (p.mes_desde, p.mes_hasta) == (1, 12)


def test_rango_de_fechas_del_anio_natural():
    assert params(anio='2028', mes_desde='2', mes_hasta='2').rango_fechas() == (date(2028, 2, 1), date(2028, 2, 29))


@pytest.mark.parametrize('valores, mensaje', [
    ({'mes_desde': '9', 'mes_hasta': '3'}, 'El periodo de meses no es válido.'),
    ({'anio': 'abc'}, 'El año no es válido.'),
    ({'anio': '26'}, 'El año no es válido.'),
])
def test_parametros_invalidos(valores, mensaje):
    with pytest.raises(ParametroInvalido, match=mensaje):
        params(**valores)


# --- FiltroPartesBuilder ----------------------------------------------------------

PERFIL = ZParte.PERNR == '00000001'


def test_siempre_incluye_el_filtro_de_perfil():
    assert sql(FiltroPartesBuilder(PERFIL).construir()) == ["zparte.`PERNR` = '00000001'"]


def test_ignora_criterios_vacios():
    condiciones = FiltroPartesBuilder(true()).departamento('').pernr('').estado('').ejercicio('').construir()
    assert len(condiciones) == 1


def test_criterios_de_los_parametros():
    condiciones = FiltroPartesBuilder(true()).criterios(params(departamento='Operaciones', estado='A')).construir()
    assert sql(condiciones)[1:] == ["zparte.`DPTO` = 'Operaciones'", "zparte.`STAT` = 'A'"]


def test_modo_rango_de_meses():
    condiciones = FiltroPartesBuilder(true()).periodo(params(anio='2030', mes_desde='3', mes_hasta='4')).construir()
    assert sql(condiciones)[1:] == ["zparte.`EJERC` = '2030'", "zparte.`MES` IN ('03', '04')"]


def test_modo_periodo_seleccionado():
    periodo = SimpleNamespace(ID='03', EJERCICIO='2030')
    condiciones = FiltroPartesBuilder(true()).periodo(params(anio='2030'), periodo).construir()
    assert sql(condiciones)[1:] == ["zparte.`EJERC` = '2030'", "zparte.`MES` = '03'"]


def test_modo_anio_natural_usa_la_fecha_del_parte():
    periodo = SimpleNamespace(ID='03', EJERCICIO='2030')
    p = params(anio='2030', mes_desde='3', mes_hasta='3', anio_natural='true')
    condiciones = FiltroPartesBuilder(true()).periodo(p, periodo).construir()
    assert sql(condiciones)[1:] == ["zparte.`PADAT` BETWEEN '2030-03-01' AND '2030-03-31'"]


def test_condicion_libre():
    condiciones = FiltroPartesBuilder(true()).condicion(literal(1) == 1).construir()
    assert len(condiciones) == 2


# --- SP ---------------------------------------------------------------------------

def test_marcado_solo_admite_valores_activados():
    # Sin funciones sobre la columna, para que pueda usar un índice
    assert sql([marcado(ZParte.SP)]) == ["zparte.`SP` IN ('t', 'X', '1', 'S')"]


@pytest.mark.parametrize('fecha, meses, esperado', [
    ('2026-10-03', 12, '2025-10-03'),
    ('2026-10-03', 24, '2024-10-03'),
    ('2026-03-31', 1, '2026-02-28'),   # febrero no tiene 31
    ('2024-03-31', 1, '2024-02-29'),   # año bisiesto
    ('2026-01-15', 1, '2025-12-15'),   # cambio de año
])
def test_restar_meses(fecha, meses, esperado):
    assert restar_meses(date.fromisoformat(fecha), meses).isoformat() == esperado

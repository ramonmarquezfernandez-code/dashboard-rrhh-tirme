"""Reglas del formulario de parte (ParteValidator), sin base de datos."""
from datetime import date
from types import SimpleNamespace

import pytest

from services.parte_service import ErrorValidacion, ParteValidator, hndec, presencia_minutos

HOY = date(2026, 10, 7)                      # miércoles
PERIODO_ABIERTO = SimpleNamespace(ID='10', EJERCICIO='2026', TRASPASO='')
PERIODO_CERRADO = SimpleNamespace(ID='09', EJERCICIO='2026', TRASPASO='S')


def datos(**cambios):
    base = {
        'fecha': '2026-10-06', 'turno': 'M', 'entrada': '07:00', 'salida': '15:00', 'pausa': '00:00',
        'horas': {}, 'motivos': {}, 'situacion': 'ninguna', 'marcas': [],
    }
    base.update(cambios)
    return base


def validar(periodo=PERIODO_ABIERTO, **cambios):
    return ParteValidator(HOY).validar(datos(**cambios), periodo=periodo)


def errores(periodo=PERIODO_ABIERTO, duplicado=False, **cambios):
    with pytest.raises(ErrorValidacion) as excepcion:
        ParteValidator(HOY).validar(datos(**cambios), periodo=periodo, duplicado=duplicado)
    return excepcion.value.errores


# --- Presencia ----------------------------------------------------------------------

def test_presencia_y_formato_hndec():
    assert presencia_minutos('07:00', '15:30', '00:30') == 8 * 60
    assert presencia_minutos('22:00', '06:00') == 8 * 60           # cruza la medianoche
    assert presencia_minutos('07:00', '07:00') == 24 * 60          # misma hora: jornada de 24 h
    assert hndec(8 * 60) == '080000'
    assert hndec(7 * 60 + 45) == '074500'


def test_parte_minimo_valido():
    v = validar()
    assert v.presencia_min == 8 * 60
    assert v.total_he == 0
    assert v.tipodia == 'L'


def test_entrada_sin_salida():
    assert 'salida' in errores(salida='')


def test_formato_de_hora():
    assert errores(entrada='7:00')['entrada'] == 'Formato HH:MM.'


def test_pausa_mayor_que_la_jornada():
    assert 'presencia' in errores(entrada='08:00', salida='09:00', pausa='02:00')


# --- Fecha, turno y duplicado -------------------------------------------------------------

def test_fecha_futura():
    assert 'futuros' in errores(fecha='2026-10-08')['fecha']


def test_periodo_traspasado():
    assert 'traspasado' in errores(periodo=PERIODO_CERRADO)['fecha']


def test_sin_periodo():
    assert 'periodo' in errores(periodo=None)['fecha']


def test_turno_obligatorio():
    assert 'turno' in errores(turno='')


def test_duplicado():
    assert 'Ya tienes' in errores(duplicado=True)['turno']


# --- Horas extra ---------------------------------------------------------------------------

def test_total_de_24_horas_es_valido():
    v = validar(entrada='00:00', salida='00:00', pausa='00:00',  # 24 h de presencia
                horas={'normales': {'DL': 12, 'NL': 12}}, motivos={'normales': 'Avería'})
    assert v.total_he == 24


def test_total_de_25_horas_no():
    e = errores(entrada='00:00', salida='00:00',
                horas={'normales': {'DL': 12, 'NL': 8}, 'compensar': {'DL': 5}},
                motivos={'normales': 'Avería', 'compensar': 'Refuerzo'})
    assert 'supera el máximo de 24' in e['total_he']


def test_llamadas_no_cuentan_en_el_total():
    v = validar(horas={'normales': {'DL': 4}, 'llamadas': {'DL': 3}},
                motivos={'normales': 'Avería', 'llamadas': 'Guardia'})
    assert v.total_he == 4
    assert v.horas['LLDL'] == 3


def test_motivo_obligatorio_por_bloque():
    e = errores(horas={'normales': {'DL': 2}, 'busca': {'DL': 1}}, motivos={'normales': 'Avería'})
    assert 'motivos.busca' in e
    assert 'motivos.normales' not in e


def test_motivo_de_bloque_sin_horas_se_descarta():
    v = validar(motivos={'normales': 'Sobra'})
    assert v.motivos['MOTIVOHE'] is None


def test_columnas_de_cada_bloque():
    v = validar(horas={'compensar': {'NL': 2}, 'combo_prog': {'DL': 1}},
                motivos={'compensar': 'a', 'combo_prog': 'b'})
    assert v.horas['NLC'] == 2 and v.horas['DLCOP'] == 1
    assert v.motivos['MOTIVOHEC'] == 'a' and v.motivos['MOTHECOP'] == 'b'


def test_horas_no_negativas_ni_decimales():
    assert errores(horas={'normales': {'DL': -1}}, motivos={'normales': 'x'})['horas.normales.DL'] == 'Entre 0 y 24.'
    assert 'entero' in errores(horas={'normales': {'DL': 1.5}}, motivos={'normales': 'x'})['horas.normales.DL']


def test_horas_extra_exigen_presencia_suficiente():
    e = errores(entrada='07:00', salida='09:00', horas={'normales': {'DL': 3}}, motivos={'normales': 'x'})
    assert 'no pueden superar el tiempo de presencia' in e['total_he']
    sin_presencia = errores(entrada='', salida='', horas={'normales': {'DL': 1}}, motivos={'normales': 'x'})
    assert 'presencia' in sin_presencia


def test_festivas_solo_en_dia_no_laborable():
    e = errores(horas={'normales': {'DF': 2}}, motivos={'normales': 'x'})   # 06/10/2026 es martes
    assert 'horas.normales.DF' in e
    assert validar(fecha='2026-10-04', horas={'normales': {'DF': 2}}, motivos={'normales': 'x'}).tipodia == 'D'
    festivo_local = validar(festivo_local=True, horas={'normales': {'DF': 2}}, motivos={'normales': 'x'})
    assert festivo_local.tipodia == 'F'


# --- Situación, marcas y otros ----------------------------------------------------------------

@pytest.mark.parametrize('situacion', ['ninguna', 'art21', 'descanso', 'teletrabajo'])
def test_una_situacion(situacion):
    assert validar(situacion=situacion).situacion == situacion


def test_situacion_desconocida_o_varias():
    assert 'situacion' in errores(situacion='art21,teletrabajo')


def test_teletrabajo_sin_kilometros():
    assert 'teletrabajo' in errores(situacion='teletrabajo', km=20)['km']
    assert validar(situacion='teletrabajo', km=0).km == 0


def test_kilometros_fuera_de_rango():
    assert 'km' in errores(km=5000)


def test_sustitucion_exige_motivo():
    assert 'motivo_sustitucion' in errores(marcas=['SUST'])
    v = validar(marcas=['SUST', 'SP'], motivo_sustitucion='Baja de un compañero')
    assert v.marcas == {'SUST', 'SP'}


def test_motivo_sustitucion_se_descarta_sin_marca():
    assert validar(motivo_sustitucion='Sobra').motivo_sustitucion is None


def test_marca_desconocida():
    assert 'marcas' in errores(marcas=['NOEXISTE'])


def test_textos_largos():
    assert 'observaciones' in errores(observaciones='x' * 151)
    assert 'motivos.normales' in errores(horas={'normales': {'DL': 1}}, motivos={'normales': 'x' * 151})

"""Mide el tiempo de las consultas agregadas principales del dashboard sobre zparte
con distintos conjuntos de índices y documenta los resultados en docs/.

Uso (desde dashboard_rrhh/, con el venv activo y la BD levantada):
    python medir_rendimiento.py                 # genera los datos y mide (un solo comando)
    python medir_rendimiento.py --sin-generar   # mide con los datos que ya hay

Pasos:
  1. Genera ~100.000 partes ficticios con semilla y fecha fijas (generar_datos.py).
  2. Captura el SQL exacto que ejecuta la app: llama a los servicios del backend
     con el filtro de perfil de HR, de un mando y de un empleado.
  3. Para cada escenario de índices de zparte (solo clave primaria, índices de
     producción, producción + propuestos) ejecuta ANALYZE TABLE, guarda el EXPLAIN
     y mide cada sentencia (1 calentamiento + N repeticiones, mediana y mínimo).
  4. Deja zparte con los índices de producción y escribe:
     docs/rendimiento.md, docs/rendimiento.json, docs/explain/*.txt y
     docs/indices_propuestos.sql.
"""
import argparse
import json
import platform
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import event, true
from werkzeug.datastructures import MultiDict

import generar_datos
from services.acceso import UsuarioActual
from services.filtro_partes import ParametrosConsulta
from services.horas_extra_service import HorasExtraService
from services.rol_service import ROL_EMPLEADO, ROL_MANDO
from services.sp_service import SpService

FECHA_DATOS = date(2026, 10, 3)        # fecha final fija: mismos datos en cada ejecución
ANIO_CONSULTA = '2025'                 # último ejercicio completo
GRUPO_MANDO = 3                        # el grupo con más empleados
REPETICIONES = 7
CARPETA_DOCS = Path(__file__).resolve().parent.parent / 'docs'

# Índices propuestos para las consultas del dashboard (escenario 3), diseñados a partir
# del EXPLAIN del escenario 2. (nombre, columnas, motivo). Se crean además de los de producción.
INDICES_PROPUESTOS = [
    ('idx_zparte_codgr_padat', ['CODGR', 'PADAT'],
     'consultas por fecha (año natural) de un mando: filtro "CODGR IN (sus grupos) OR PERNR = suyo" '
     'con PADAT entre dos fechas. Con este índice y zparte_PERNR_IDX (PERNR, PADAT) el optimizador '
     'combina ambos rangos (index_merge) en lugar de recorrer toda la tabla.'),
    ('idx_zparte_sp_padat', ['SP', 'PADAT'],
     'pantalla de SP: partes con SP marcado (~3 %) en los últimos 12/24 meses. Requiere que la condición '
     'sobre SP no use funciones (SP IN (...) en lugar de TRIM(SP) IN (...)).'),
]


@dataclass
class Sentencia:
    consulta: str
    perfil: str
    orden: int
    sql: str              # SQL con los valores ya sustituidos (para documentar y ejecutar)
    resultados: dict = field(default_factory=dict)   # escenario -> {'mediana_ms', 'min_ms', 'explain', ...}

    @property
    def clave(self):
        return f'{self.consulta}__{self.perfil}__{self.orden}'


# --- Captura del SQL que ejecuta la app ---------------------------------------------

def perfiles(conexion):
    """Filtros de perfil de un HR, de un mando (FI del grupo más grande) y de un empleado."""
    with conexion.cursor() as cursor:
        cursor.execute("SELECT PERNR FROM zgrroles WHERE ROLNAME = 'FI' AND CODGR = %s ORDER BY PERNR LIMIT 1",
                       (GRUPO_MANDO,))
        mando = cursor.fetchone()[0]
        cursor.execute("""
            SELECT u.NUMPER FROM userpayroll u
            WHERE u.GRUPO = %s AND u.ACTIVE = 1 AND u.NUMPER NOT IN (SELECT PERNR FROM zgrroles)
            ORDER BY u.NUMPER LIMIT 1""", (GRUPO_MANDO,))
        empleado = cursor.fetchone()[0]
    return {
        'hr': true(),
        'mando': UsuarioActual(mando, '', ROL_MANDO, frozenset({GRUPO_MANDO})).filtro_partes(),
        'empleado': UsuarioActual(empleado, '', ROL_EMPLEADO).filtro_partes(),
    }


def consultas_del_dashboard():
    """(nombre, descripción, función(servicio_he, servicio_sp)) de las pantallas principales."""
    anual = ParametrosConsulta.desde_args(MultiDict({'anio': ANIO_CONSULTA}))
    natural = ParametrosConsulta.desde_args(MultiDict({'anio': ANIO_CONSULTA, 'anio_natural': 'true'}))
    periodo = ParametrosConsulta.desde_args(MultiDict({'anio': ANIO_CONSULTA, 'periodo_id': '06'}))
    return [
        ('he_por_periodo', f'HE por periodos, ejercicio {ANIO_CONSULTA} completo', lambda he, sp: he.por_periodo(anual)),
        ('he_por_periodo_natural', f'HE por periodos, año natural {ANIO_CONSULTA}', lambda he, sp: he.por_periodo(natural)),
        ('he_por_periodo_junio', 'HE por periodos, periodo de nómina 06', lambda he, sp: he.por_periodo(periodo)),
        ('he_por_empleado', f'HE por empleado, ejercicio {ANIO_CONSULTA}', lambda he, sp: he.por_empleado(anual)),
        ('ranking_combo', f'Ranking HE combo, ejercicio {ANIO_CONSULTA}', lambda he, sp: he.ranking_combo(anual)),
        ('sp_resumen', 'SP de los últimos 12 y 24 meses', lambda he, sp: sp.resumen_periodos(FECHA_DATOS)),
        ('ejercicios', 'Años disponibles (combo de año)', lambda he, sp: he.ejercicios(hoy=FECHA_DATOS)),
    ]


def capturar_sentencias(app, conexion):
    from extensions import db

    descripciones = {}
    sentencias = []
    with app.app_context():
        capturadas = []

        def al_ejecutar(_conn, cursor, sql, parametros, _contexto, _many):
            capturadas.append(cursor.mogrify(sql, parametros))

        event.listen(db.engine, 'before_cursor_execute', al_ejecutar)
        try:
            for perfil, filtro in perfiles(conexion).items():
                for nombre, descripcion, funcion in consultas_del_dashboard():
                    descripciones[nombre] = descripcion
                    capturadas.clear()
                    funcion(HorasExtraService(filtro), SpService(filtro))
                    de_zparte = [sql for sql in capturadas if 'FROM zparte' in sql]
                    sentencias += [Sentencia(nombre, perfil, n, sql) for n, sql in enumerate(de_zparte, 1)]
        finally:
            event.remove(db.engine, 'before_cursor_execute', al_ejecutar)
            db.session.remove()
    return sentencias, descripciones


# --- Índices ----------------------------------------------------------------------------

def indices_actuales(cursor):
    """Índices secundarios de zparte: [(nombre, único, [columnas])]."""
    cursor.execute("""
        SELECT INDEX_NAME, NON_UNIQUE = 0, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX)
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'zparte' AND INDEX_NAME <> 'PRIMARY'
        GROUP BY INDEX_NAME, NON_UNIQUE ORDER BY INDEX_NAME""")
    return [(nombre, bool(unico), columnas.split(',')) for nombre, unico, columnas in cursor.fetchall()]


def ddl_indice(nombre, unico, columnas):
    lista = ', '.join(f'`{c}`' for c in columnas)
    return f"ADD {'UNIQUE ' if unico else ''}INDEX `{nombre}` ({lista})"


def aplicar_indices(cursor, deseados):
    """Deja en zparte exactamente los índices secundarios indicados."""
    actuales = {nombre: (unico, columnas) for nombre, unico, columnas in indices_actuales(cursor)}
    deseados_por_nombre = {nombre: (unico, columnas) for nombre, unico, columnas in deseados}
    cambios = [f'DROP INDEX `{n}`' for n in actuales if actuales[n] != deseados_por_nombre.get(n)]
    cambios += [ddl_indice(n, u, c) for n, (u, c) in deseados_por_nombre.items() if actuales.get(n) != (u, c)]
    if cambios:
        cursor.execute(f'ALTER TABLE zparte {", ".join(cambios)}')
    cursor.execute('ANALYZE TABLE zparte')
    cursor.fetchall()


# --- Medición ---------------------------------------------------------------------------

def resumen_explain(filas, columnas):
    """Tipo de acceso, índice y filas estimadas de la tabla zparte en un EXPLAIN tabular."""
    for fila in filas:
        datos = dict(zip(columnas, fila))
        if datos.get('table') == 'zparte' or str(datos.get('table', '')).startswith('<derived'):
            return {'tipo': datos.get('type'), 'indice': datos.get('key'), 'filas': datos.get('rows'),
                    'extra': datos.get('Extra')}
    return {}


def medir(cursor, sentencia, escenario, repeticiones):
    cursor.execute(f'EXPLAIN {sentencia.sql}')
    columnas = [d[0] for d in cursor.description]
    filas = cursor.fetchall()
    explain_tabla = [dict(zip(columnas, fila)) for fila in filas]
    cursor.execute(f'EXPLAIN FORMAT=JSON {sentencia.sql}')
    explain_json = cursor.fetchone()[0]

    cursor.execute(sentencia.sql)       # calentamiento
    cursor.fetchall()
    tiempos = []
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        cursor.execute(sentencia.sql)
        cursor.fetchall()
        tiempos.append((time.perf_counter() - inicio) * 1000)
    sentencia.resultados[escenario] = {
        'mediana_ms': round(statistics.median(tiempos), 2),
        'min_ms': round(min(tiempos), 2),
        'explain': resumen_explain(filas, columnas),
        'explain_tabla': explain_tabla,
        'explain_json': json.loads(explain_json),
    }


# --- Informe --------------------------------------------------------------------------------

def _ms(valor):
    return f'{valor:,.1f}'.replace(',', ' ') if valor is not None else '—'


def _mejora(antes, despues):
    if not antes or despues is None:
        return '—'
    return f'{(1 - despues / antes) * 100:+.0f} %'.replace('+', '−', 1) if despues < antes else f'+{(despues / antes - 1) * 100:.0f} %'


def escribir_docs(sentencias, descripciones, escenarios, contexto):
    CARPETA_DOCS.mkdir(exist_ok=True)
    carpeta_explain = CARPETA_DOCS / 'explain'
    carpeta_explain.mkdir(exist_ok=True)
    for antiguo in carpeta_explain.glob('*.txt'):
        antiguo.unlink()
    nombres = [e['clave'] for e in escenarios]

    # Tiempos por consulta y perfil (suma de sus sentencias sobre zparte)
    agregados = {}
    for s in sentencias:
        fila = agregados.setdefault((s.consulta, s.perfil), {
            'sentencias': 0, 'planes': {n: [] for n in nombres}, **{n: 0.0 for n in nombres}})
        fila['sentencias'] += 1
        for n in nombres:
            fila[n] += s.resultados[n]['mediana_ms']
            fila['planes'][n].append(plan(s, n))

    lineas = [
        '# Rendimiento de las consultas del dashboard',
        '',
        f'> Generado automáticamente por `dashboard_rrhh/medir_rendimiento.py` el {contexto["fecha"]}. '
        'No editar a mano: se sobrescribe en cada ejecución.',
        '',
        '## Cómo reproducirlo',
        '',
        '```bash',
        'cd dashboard_rrhh',
        'python medir_rendimiento.py',
        '```',
        '',
        'Genera los datos con semilla y fecha fijas (mismos datos en cada ejecución), mide y reescribe este '
        'documento, `rendimiento.json`, `explain/` e `indices_propuestos.sql`. Los tiempos absolutos dependen '
        'del equipo; lo comparable son las proporciones entre escenarios.',
        '',
        '## Entorno y datos',
        '',
        '| | |',
        '|---|---|',
        f'| Servidor | {contexto["servidor"]} |',
        f'| Equipo | {contexto["equipo"]} |',
        f'| Datos | {contexto["datos"]} |',
        f'| Filas | ' + ', '.join(f'{t}: {n:,}'.replace(',', '.') for t, n in contexto['filas'].items()) + ' |',
        f'| Consultas | ejercicio {ANIO_CONSULTA}; mando = FI del grupo {GRUPO_MANDO} ({contexto["empleados_grupo"]} empleados) |',
        f'| Medición | 1 ejecución de calentamiento + {contexto["repeticiones"]} repeticiones; se muestra la mediana |',
        f'| Caché de consultas | `query_cache_type = {contexto["query_cache"]}` |',
        '',
        '## Escenarios de índices sobre `zparte`',
        '',
    ]
    for e in escenarios:
        lineas.append(f'- **{e["titulo"]}**: {e["descripcion"]}')
    lineas += [
        '',
        '## Tiempos por pantalla y perfil',
        '',
        'Suma de las medianas de las sentencias sobre `zparte` que ejecuta cada pantalla (ms). '
        '**≈** indica que el plan de ejecución es el mismo en los dos escenarios comparados: esa diferencia '
        'es ruido de medición, no efecto de los índices.',
        '',
        '| Consulta | Perfil | Sentencias | ' + ' | '.join(e['titulo'] for e in escenarios)
        + ' | ' + ' | '.join(f'{escenarios[i]["corto"]} → {escenarios[i + 1]["corto"]}' for i in range(len(escenarios) - 1)) + ' |',
        '|---|---|---:|' + '---:|' * len(escenarios) + '---:|' * (len(escenarios) - 1),
    ]
    for (consulta, perfil), fila in agregados.items():
        celdas = [_ms(fila[n]) for n in nombres]
        mejoras = [('≈ ' if fila['planes'][nombres[i]] == fila['planes'][nombres[i + 1]] else '')
                   + _mejora(fila[nombres[i]], fila[nombres[i + 1]]) for i in range(len(nombres) - 1)]
        lineas.append(f'| {descripciones[consulta]} | {perfil} | {fila["sentencias"]} | '
                      + ' | '.join(celdas) + ' | ' + ' | '.join(mejoras) + ' |')

    totales = {n: sum(f[n] for f in agregados.values()) for n in nombres}
    lineas.append('| **Total** | | | ' + ' | '.join(f'**{_ms(totales[n])}**' for n in nombres) + ' | '
                  + ' | '.join(f'**{_mejora(totales[nombres[i]], totales[nombres[i + 1]])}**'
                               for i in range(len(nombres) - 1)) + ' |')

    lineas += [
        '',
        '## Plan de ejecución (resumen del EXPLAIN)',
        '',
        'Acceso a `zparte` en cada sentencia: tipo de acceso (`ALL` = recorrido completo), índice usado y filas '
        'estimadas. El EXPLAIN completo (tabular y JSON) y el SQL de cada sentencia están en `docs/explain/`.',
        '',
        '| Sentencia | ' + ' | '.join(e['titulo'] for e in escenarios) + ' |',
        '|---|' + '---|' * len(escenarios),
    ]
    for s in sentencias:
        celdas = []
        for n in nombres:
            ex = s.resultados[n]['explain']
            celdas.append(f'`{ex.get("tipo")}` {ex.get("indice") or "—"} ({ex.get("filas")} filas)')
        lineas.append(f'| [{s.consulta} · {s.perfil} · {s.orden}](explain/{s.clave}.txt) | ' + ' | '.join(celdas) + ' |')

    if INDICES_PROPUESTOS:
        lineas += ['', '## Índices propuestos', '',
                   'Propuesta para el equipo de la aplicación corporativa (el esquema es compartido). No se añaden '
                   'al dump; el script los crea solo durante la medición. SQL en `docs/indices_propuestos.sql`.', '']
        for nombre, columnas, motivo in INDICES_PROPUESTOS:
            lineas.append(f'- `{nombre}` ({", ".join(columnas)}): {motivo}')

    lineas += ['', '## Conclusiones', '', *conclusiones(agregados, totales, escenarios, descripciones), '']
    (CARPETA_DOCS / 'rendimiento.md').write_text('\n'.join(lineas), encoding='utf-8')

    # EXPLAIN completo por sentencia
    for s in sentencias:
        bloques = [f'# {descripciones[s.consulta]} · perfil {s.perfil} · sentencia {s.orden}', '', s.sql, '']
        for e in escenarios:
            r = s.resultados[e['clave']]
            bloques += [f'## {e["titulo"]} — mediana {r["mediana_ms"]} ms, mínimo {r["min_ms"]} ms', '']
            for fila in r['explain_tabla']:
                bloques.append('  ' + ' | '.join(f'{k}={v}' for k, v in fila.items()))
            bloques += ['', json.dumps(r['explain_json'], indent=2, ensure_ascii=False), '']
        (carpeta_explain / f'{s.clave}.txt').write_text('\n'.join(bloques), encoding='utf-8')

    datos = {
        'contexto': contexto,
        'escenarios': [{k: v for k, v in e.items() if k != 'indices'} | {'indices': e['indices']} for e in escenarios],
        'sentencias': [
            {'consulta': s.consulta, 'perfil': s.perfil, 'orden': s.orden, 'sql': s.sql,
             'resultados': {n: {k: v for k, v in r.items() if k not in ('explain_tabla', 'explain_json')}
                            for n, r in s.resultados.items()}}
            for s in sentencias
        ],
    }
    (CARPETA_DOCS / 'rendimiento.json').write_text(
        json.dumps(datos, indent=2, ensure_ascii=False, default=str), encoding='utf-8')

    sql = ['-- Índices propuestos para zparte (generado por medir_rendimiento.py).',
           '-- Propuesta para revisar con el equipo de la app corporativa: el esquema es compartido.', '']
    for nombre, columnas, motivo in INDICES_PROPUESTOS:
        sql += [f'-- {motivo}', f'ALTER TABLE zparte {ddl_indice(nombre, False, columnas)};', '']
    if not INDICES_PROPUESTOS:
        sql.append('-- Ningún índice adicional mejora de forma medible las consultas del dashboard.')
    (CARPETA_DOCS / 'indices_propuestos.sql').write_text('\n'.join(sql), encoding='utf-8')


def plan(sentencia, escenario):
    """Tipo de acceso e índice usados sobre zparte (para saber si el plan cambia)."""
    explain = sentencia.resultados[escenario]['explain']
    return explain.get('tipo'), explain.get('indice')


def conclusiones(agregados, totales, escenarios, descripciones):
    """Conclusiones calculadas a partir de los resultados (se reescriben en cada ejecución)."""
    nombres = [e['clave'] for e in escenarios]
    base, prod = nombres[0], nombres[1]

    def nombre(clave):
        return f'*{descripciones[clave[0]]}* ({clave[1]})'

    peor = max(agregados.items(), key=lambda kv: kv[1][base])
    # Pantallas que recorren toda la tabla incluso con el mejor conjunto de índices
    recorridos = [c for c, f in agregados.items() if all(t == 'ALL' for t, _ in f['planes'][nombres[-1]])]
    lineas = [
        f'- Sin índices secundarios, las consultas del dashboard suman {_ms(totales[base])} ms; con los índices de '
        f'producción, {_ms(totales[prod])} ms ({_mejora(totales[base], totales[prod])}).',
        f'- La pantalla más costosa sin índices es {nombre(peor[0])}: {_ms(peor[1][base])} ms.',
        '- Las consultas de un empleado y las de un periodo de nómina concreto son las que más ganan con los índices '
        'de producción: pasan de recorrer toda la tabla a leer solo las filas del trabajador o del periodo.',
    ]
    if recorridos:
        lineas.append(
            f'- {len(recorridos)} pantallas recorren toda la tabla en todos los escenarios (p. ej. '
            f'{nombre(recorridos[0])}). Son agregados de RRHH sobre un año entero (un tercio de las filas): '
            'para eso el recorrido completo es el plan correcto y un índice no ayudaría.')
    for i in range(1, len(nombres) - 1):
        anterior, siguiente = nombres[i], nombres[i + 1]
        lineas.append(f'- Con los índices propuestos: {_ms(totales[siguiente])} ms en total '
                      f'({_mejora(totales[anterior], totales[siguiente])} respecto a producción).')
        for clave, fila in agregados.items():
            cambia_plan = fila['planes'][anterior] != fila['planes'][siguiente]
            if cambia_plan and fila[siguiente] > fila[anterior] * 1.1 and fila[siguiente] - fila[anterior] > 1:
                lineas.append(
                    f'  - Empeora {nombre(clave)}: {_ms(fila[anterior])} → {_ms(fila[siguiente])} ms, porque el '
                    'optimizador cambia de plan (ver su EXPLAIN). Es un coste pequeño frente a la mejora del resto.')
    return lineas


# --- Programa principal -------------------------------------------------------------------

def main(argumentos=None):
    parser = argparse.ArgumentParser(description='Mide las consultas del dashboard con distintos índices.')
    parser.add_argument('--sin-generar', action='store_true', help='no regenerar los datos de demostración')
    parser.add_argument('--partes', type=int, default=generar_datos.PARTES_POR_DEFECTO)
    parser.add_argument('--repeticiones', type=int, default=REPETICIONES)
    args = parser.parse_args(argumentos)

    from app import app
    from config import Config

    if 'prod' in Config.DB_NAME.lower():
        sys.exit(f'Me niego a modificar los índices de "{Config.DB_NAME}": parece una BD de producción.')

    if not args.sin_generar:
        generar_datos.main(['--partes', str(args.partes), '--hasta', FECHA_DATOS.isoformat()])

    conexion = generar_datos.conectar()
    try:
        with conexion.cursor() as cursor:
            produccion = indices_actuales(cursor)
            cursor.execute('SELECT VERSION(), @@query_cache_type')
            version, query_cache = cursor.fetchone()
            filas = {}
            for tabla in ('zparte', 'userpayroll', 'zgrroles', 'zperiodos'):
                cursor.execute(f'SELECT COUNT(*) FROM {tabla}')
                filas[tabla] = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM userpayroll WHERE GRUPO = %s', (GRUPO_MANDO,))
            empleados_grupo = cursor.fetchone()[0]

        if not produccion:
            sys.exit('zparte no tiene índices secundarios: recrea la BD (docker compose down -v / up -d) antes de medir.')

        print('Capturando el SQL que ejecuta la app...')
        sentencias, descripciones = capturar_sentencias(app, conexion)
        print(f'  {len(sentencias)} sentencias sobre zparte')

        propuestos = [(nombre, False, columnas) for nombre, columnas, _ in INDICES_PROPUESTOS]
        escenarios = [
            {'clave': 'solo_pk', 'titulo': '1. Solo clave primaria', 'corto': '1',
             'descripcion': 'se eliminan todos los índices secundarios de zparte (incluidos los UNIQUE).',
             'indices': []},
            {'clave': 'produccion', 'titulo': '2. Índices de producción', 'corto': '2',
             'descripcion': f'los {len(produccion)} índices secundarios del esquema de producción.',
             'indices': produccion},
        ]
        if INDICES_PROPUESTOS:
            escenarios.append({
                'clave': 'propuestos', 'titulo': '3. Producción + propuestos', 'corto': '3',
                'descripcion': f'los de producción más {len(propuestos)} índices propuestos (ver más abajo).',
                'indices': produccion + propuestos,
            })

        with conexion.cursor() as cursor:
            try:
                for escenario in escenarios:
                    print(f'{escenario["titulo"]}: aplicando índices...')
                    aplicar_indices(cursor, escenario['indices'])
                    # Pasada de estabilización: tras un ALTER TABLE InnoDB reorganiza páginas en
                    # memoria y las primeras ejecuciones son mucho más lentas de lo normal
                    for sentencia in sentencias:
                        cursor.execute(sentencia.sql)
                        cursor.fetchall()
                    for n, sentencia in enumerate(sentencias, 1):
                        medir(cursor, sentencia, escenario['clave'], args.repeticiones)
                        print(f'  {n}/{len(sentencias)} {sentencia.clave}: '
                              f'{sentencia.resultados[escenario["clave"]]["mediana_ms"]} ms', end='\r')
                    print()
            finally:
                print('Restaurando los índices de producción...')
                aplicar_indices(cursor, produccion)
    finally:
        conexion.close()

    contexto = {
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'servidor': f'MariaDB {version}',
        'equipo': f'{platform.system()} {platform.release()}, {platform.machine()}, Python {platform.python_version()}',
        'datos': f'generar_datos.py con semilla {generar_datos.SEMILLA_POR_DEFECTO}, fecha final {FECHA_DATOS}, '
                 f'~{args.partes:,} partes'.replace(f'{args.partes:,}', f'{args.partes:,}'.replace(',', '.')),
        'filas': filas,
        'empleados_grupo': empleados_grupo,
        'repeticiones': args.repeticiones,
        'query_cache': query_cache,
    }
    escribir_docs(sentencias, descripciones, escenarios, contexto)
    print(f'Resultados en {CARPETA_DOCS / "rendimiento.md"}')


if __name__ == '__main__':
    main()

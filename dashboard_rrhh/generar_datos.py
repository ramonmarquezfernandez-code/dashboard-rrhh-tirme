"""Genera datos ficticios de demostración: 250 empleados, 25 grupos y unos
100.000 partes repartidos entre el 1 de enero de hace dos años y hoy.

Uso (desde dashboard_rrhh/, con el venv activo y la BD levantada):
    python generar_datos.py [--partes 100000] [--semilla 2026] [--hasta AAAA-MM-DD]

ATENCIÓN: sustituye los datos de la BD configurada en .env (DB_NAME): vacía
zparte, zgrroles, userpayroll y zperiodos y rehace grupos, áreas y
departamentos. Se niega a ejecutarse sobre una BD cuyo nombre contenga "prod".

Todos los nombres, números de personal y correos son inventados (LOPD). Las
proporciones (turnos, estados, horas extra, marcas, periodos de nómina, roles,
bajas) imitan las de la explotación real, obtenidas únicamente como estadísticas
agregadas, sin copiar ningún registro.

Con la misma semilla y la misma fecha final se generan exactamente los mismos
datos (la "huella" del resumen lo permite comprobar). Los usuarios de prueba
00000001-00000005 se mantienen con sus correos, grupos y roles (ver seed.py).
"""
import argparse
import hashlib
import random
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta

from seed import ESTADOS, PASSWORD_PRUEBA, USUARIOS as USUARIOS_PRUEBA
from services.auth_service import AuthService
from services.calendario import tipo_dia

PARTES_POR_DEFECTO = 100_000
SEMILLA_POR_DEFECTO = 2026
TAMANO_LOTE = 5_000
MANDT_INICIAL = 1_700_000_000_000
DIA_INICIO_PERIODO = 11         # los periodos de nómina van del 11 de un mes al 10 del siguiente
PROPORCION_INACTIVOS = 0.20     # empleados que ya no están en la empresa (dejan de tener partes)

AREAS = [
    (100, 'Desarrollo Software'),
    (200, 'Mantenimiento y Planta'),
    (300, 'Recogida de Residuos'),
    (400, 'Tratamiento y Valorización'),
    (500, 'Administración y Finanzas'),
    (600, 'Logística y Transporte'),
]

# (código, nombre, área)
DEPARTAMENTOS = [
    (10, 'Sistemas e IT', 100),
    (20, 'Operaciones', 200),
    (30, 'Recogida Norte', 300),
    (40, 'Recogida Sur', 300),
    (50, 'Planta de Clasificación', 400),
    (60, 'Valorización Energética', 400),
    (70, 'Compostaje', 400),
    (80, 'Mantenimiento Mecánico', 200),
    (90, 'Mantenimiento Eléctrico', 200),
    (110, 'Contabilidad', 500),
    (120, 'Recursos Humanos', 500),
    (130, 'Flota y Talleres', 600),
]

# (código, nombre, departamento, turnos, empleados). Tamaños desiguales, como en la
# plantilla real. 'M' = oficina (solo laborables); 'MT'/'MTN' = turnos rotativos
# semanales (sobre todo de mañana) que trabajan además uno de cada dos fines de semana.
GRUPOS = [
    (1, 'Grupo Técnico A', 10, 'M', 6),
    (2, 'Grupo Operativo B', 20, 'MT', 12),
    (3, 'Recogida Norte - Equipo 1', 30, 'MTN', 26),
    (4, 'Recogida Norte - Equipo 2', 30, 'MTN', 22),
    (5, 'Recogida Norte - Equipo 3', 30, 'MT', 14),
    (6, 'Recogida Sur - Equipo 1', 40, 'MTN', 21),
    (7, 'Recogida Sur - Equipo 2', 40, 'MTN', 18),
    (8, 'Recogida Sur - Equipo 3', 40, 'MT', 10),
    (9, 'Clasificación - Línea 1', 50, 'MTN', 12),
    (10, 'Clasificación - Línea 2', 50, 'MTN', 10),
    (11, 'Clasificación - Línea 3', 50, 'MT', 6),
    (12, 'Valorización - Turno A', 60, 'MTN', 8),
    (13, 'Valorización - Turno B', 60, 'MTN', 8),
    (14, 'Valorización - Turno C', 60, 'MTN', 8),
    (15, 'Compostaje - Equipo 1', 70, 'MT', 6),
    (16, 'Compostaje - Equipo 2', 70, 'MT', 5),
    (17, 'Mant. Mecánico - Taller', 80, 'MT', 7),
    (18, 'Mant. Mecánico - Guardia', 80, 'MTN', 5),
    (19, 'Mant. Eléctrico - Taller', 90, 'MT', 6),
    (20, 'Mant. Eléctrico - Guardia', 90, 'MTN', 4),
    (21, 'Contabilidad', 110, 'M', 5),
    (22, 'Recursos Humanos', 120, 'M', 4),
    (23, 'Flota - Conductores', 130, 'MTN', 17),
    (24, 'Flota - Taller', 130, 'MT', 7),
    (25, 'Sistemas e IT - Soporte', 10, 'M', 3),
]
EMPLEADOS_TOTALES = sum(grupo[4] for grupo in GRUPOS)   # 250
GRUPO_RRHH = 22

# Categorías (zparte.CATEG, máx. 20 caracteres) según el tipo de grupo
CATEGORIAS_OFICINA = ['Administrativo', 'Técnico', 'Analista Programador', 'Jefe de Sección']
CATEGORIAS_CAMPO = ['Conductor', 'Peón', 'Operario de Planta', 'Oficial 1ª', 'Encargado', 'Mecánico', 'Electricista']

NOMBRES = [
    'Antonio', 'José', 'Manuel', 'Francisco', 'David', 'Juan', 'Javier', 'Daniel', 'Carlos', 'Miguel',
    'Rafael', 'Pedro', 'Pablo', 'Sergio', 'Jorge', 'Alberto', 'Luis', 'Fernando', 'Andrés', 'Rubén',
    'María', 'Carmen', 'Ana', 'Isabel', 'Laura', 'Cristina', 'Marta', 'Lucía', 'Elena', 'Pilar',
    'Raquel', 'Sara', 'Paula', 'Rosa', 'Silvia', 'Patricia', 'Beatriz', 'Núria', 'Margalida', 'Catalina',
]
APELLIDOS = [
    'García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez', 'Sánchez', 'Pérez', 'Gómez', 'Martín',
    'Jiménez', 'Ruiz', 'Hernández', 'Díaz', 'Moreno', 'Muñoz', 'Álvarez', 'Romero', 'Alonso', 'Gutiérrez',
    'Navarro', 'Torres', 'Domínguez', 'Vázquez', 'Ramos', 'Gil', 'Ramírez', 'Serrano', 'Blanco', 'Molina',
    'Morales', 'Suárez', 'Ortega', 'Delgado', 'Castro', 'Ortiz', 'Rubio', 'Marín', 'Sanz', 'Iglesias',
    'Ferrer', 'Vidal', 'Bonet', 'Pons', 'Mas', 'Coll', 'Sastre', 'Oliver', 'Riera', 'Bauzà',
]
NOMBRES_MES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
               'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

# Rotación semanal de los grupos de turnos
ROTACION_TURNOS = {'MT': 'MMMMT', 'MTN': 'MMMMMTN'}

# --- Horas extra ---------------------------------------------------------------------
# Solo ~6 % de los partes tiene alguna hora extra. Peso relativo de cada tipo (sufijo
# de columna) y valores típicos de horas, según la distribución observada.
PROBABILIDAD_HE = 0.055
TIPOS_HE = {            # sufijo: (peso, valores, pesos de los valores)
    '': (45, (1, 2, 3, 4, 5, 8), (25, 17, 33, 8, 8, 9)),        # normales
    'C': (37, (1, 2, 3, 4, 8), (38, 23, 23, 8, 8)),               # a compensar
    'B': (8, (1, 2, 3, 4, 5), (40, 28, 15, 10, 7)),               # busca
    'BN': (6, (1, 2), (45, 55)),                                  # busca no pagada
    'CO': (5, (1, 2, 3, 4, 8), (30, 25, 15, 10, 20)),             # combo
    'COP': (0.5, (8, 5), (90, 10)),                               # combo programadas
}
VALORES_FESTIVO = ((8, 4, 1, 6, 3), (60, 15, 10, 8, 7))          # en festivo suele ser jornada completa
PROBABILIDAD_LLAMADA = 0.008
VALORES_LLAMADA = ((1, 2, 3), (85, 11, 4))

# Marcas char(1): valor 'X' y su probabilidad (el resto NULL)
MARCAS_X = {'SP': 0.026, 'SUST': 0.026, 'BLV': 0.144, 'BSDF': 0.072, 'PP': 0.015, 'D': 0.015, 'CP': 0.005, 'PN': 0.002}

COLUMNAS_HE = (
    'DL', 'DF', 'NL', 'NF', 'DLB', 'DFB', 'NLB', 'NFB', 'DLF', 'DFF', 'NLF', 'NFF',
    'DLC', 'DFC', 'NLC', 'NFC', 'LLDL', 'LLDF', 'LLNL', 'LLNF', 'DLCO', 'DFCO', 'NLCO', 'NFCO',
    'DLBN', 'DFBN', 'NLBN', 'NFBN', 'DLCOP', 'DFCOP', 'NLCOP', 'NFCOP',
)
COLUMNAS_PARTE = (
    'MANDT', 'PERNR', 'PADAT', 'TIPO', 'TURNO', 'REDAT', 'UPDAT', 'MODIF', 'MES', 'EJERC', 'STAT', 'PAJOB',
    'CODGR', 'DPTO', 'CATEG', 'TIPODIA', 'PERNRCR', 'CRDAT', 'PERNRVB', 'VBDAT', 'PERNRFI', 'FIDAT',
    'PERNRHR', 'HRDAT', 'HN', *COLUMNAS_HE, *MARCAS_X, 'PA', 'KM', 'TIPOTURNO',
    'TELETRABAJO', 'DESCANSO', 'USER_ID',
)


@dataclass
class Empleado:
    pernr: str
    nombre: str
    apellidos: str
    email: str
    grupo: int
    activo: bool = True
    categoria: str = ''
    baja_desde: date | None = None   # inactivos: último día con partes
    desfase_turno: int = 0


@dataclass
class Resumen:
    empleados: int = 0
    inactivos: int = 0
    grupos: int = 0
    roles: int = 0
    partes: int = 0
    partes_por_ejercicio: dict = field(default_factory=dict)
    partes_con_he: int = 0
    desde: date | None = None
    hasta: date | None = None
    huella: str = ''
    segundos: float = 0.0


def _sin_acentos(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
    return texto.lower().replace(' ', '')


def periodo_de(dia):
    """Periodo de nómina (MES, EJERC) al que pertenece una fecha: del día 11 de un mes
    al 10 del siguiente. El periodo '01' de un año empieza el 11 de diciembre anterior."""
    mes, anio = dia.month, dia.year
    if dia.day >= DIA_INICIO_PERIODO:
        mes += 1
        if mes == 13:
            mes, anio = 1, anio + 1
    return f'{mes:02d}', str(anio)


def limites_periodo(mes, anio):
    """Fechas de inicio y fin del periodo de nómina (mes, año)."""
    fin = date(anio, mes, DIA_INICIO_PERIODO - 1)
    inicio = date(anio - 1, 12, DIA_INICIO_PERIODO) if mes == 1 else date(anio, mes - 1, DIA_INICIO_PERIODO)
    return inicio, fin


class GeneradorDatos:
    """Crea catálogos, empleados, roles, periodos y partes sobre una conexión DB-API (PyMySQL)."""

    def __init__(self, conexion, partes=PARTES_POR_DEFECTO, semilla=SEMILLA_POR_DEFECTO, hasta=None):
        self.conexion = conexion
        self.objetivo_partes = partes
        self.semilla = semilla
        self.hasta = hasta or date.today()
        self.desde = date(self.hasta.year - 2, 1, 1)
        self.rng = random.Random(semilla)
        self.grupos = {codigo: (nombre, dpto, turnos) for codigo, nombre, dpto, turnos, _ in GRUPOS}
        self.departamentos = {codigo: (nombre, area) for codigo, nombre, area in DEPARTAMENTOS}
        self.empleados: list[Empleado] = []
        self.roles: list[tuple[int, str, str]] = []
        self.firmantes: dict[int, dict[str, str]] = {}   # grupo -> {'VB': pernr, 'FI': pernr}
        self.hr: list[str] = []

    # --- API pública -----------------------------------------------------------

    def generar(self):
        inicio = time.perf_counter()
        resumen = Resumen(desde=self.desde, hasta=self.hasta)
        self._preparar_empleados()
        self._preparar_roles()
        self._dar_de_baja()
        with self.conexion.cursor() as cursor:
            self._limpiar(cursor)
            self._catalogos(cursor)
            self._insertar_empleados_y_roles(cursor)
            self._periodos(cursor)
            self.conexion.commit()
            self._crear_partes(cursor, resumen)
            cursor.execute('ANALYZE TABLE zparte, userpayroll, zgrroles')
            cursor.fetchall()
        self.conexion.commit()
        resumen.empleados = len(self.empleados)
        resumen.inactivos = sum(not e.activo for e in self.empleados)
        resumen.grupos = len(GRUPOS)
        resumen.roles = len(self.roles)
        resumen.segundos = time.perf_counter() - inicio
        return resumen

    # --- Preparación en memoria -------------------------------------------------

    def _preparar_empleados(self):
        prueba = {numper: (nombre, apellidos, email, grupo)
                  for numper, nombre, apellidos, email, grupo, *_ in USUARIOS_PRUEBA}
        plazas = []
        for codigo, *_, tamano in GRUPOS:
            plazas += [codigo] * (tamano - sum(1 for datos in prueba.values() if datos[3] == codigo))
        self.rng.shuffle(plazas)

        for numero in range(1, EMPLEADOS_TOTALES + 1):
            pernr = f'{numero:08d}'
            if pernr in prueba:
                nombre, apellidos, email, grupo = prueba[pernr]
            else:
                nombre = self.rng.choice(NOMBRES)
                apellido1, apellido2 = self.rng.sample(APELLIDOS, 2)
                apellidos = f'{apellido1} {apellido2}'
                email = f'{_sin_acentos(nombre)}.{_sin_acentos(apellido1)}.{numero:03d}@empresa.local'
                grupo = plazas.pop()
            turnos = self.grupos[grupo][2]
            self.empleados.append(Empleado(
                pernr=pernr, nombre=nombre, apellidos=apellidos, email=email, grupo=grupo,
                categoria=self.rng.choice(CATEGORIAS_OFICINA if turnos == 'M' else CATEGORIAS_CAMPO),
                desfase_turno=self.rng.randrange(3),
            ))

    def _preparar_roles(self):
        """FI en todos los grupos (1-2), VB solo en algunos y HR con una fila por grupo,
        como en la tabla real. Se respetan los roles de los usuarios de prueba."""
        prueba = {u[0] for u in USUARIOS_PRUEBA}
        for numper, *_, roles in USUARIOS_PRUEBA:
            for rolname, codgr in roles:
                self.roles.append((codgr, numper, rolname))
                if rolname == 'HR':
                    if numper not in self.hr:
                        self.hr.append(numper)
                else:
                    self.firmantes.setdefault(codgr, {})[rolname] = numper

        for codigo, *_ in GRUPOS:
            miembros = [e.pernr for e in self.empleados if e.grupo == codigo and e.pernr not in prueba]
            asignados = self.firmantes.setdefault(codigo, {})
            libres = [m for m in miembros if m not in asignados.values()]
            if 'FI' not in asignados:
                for elegido in self.rng.sample(libres, 2 if len(libres) > 8 else 1):
                    asignados.setdefault('FI', elegido)
                    self.roles.append((codigo, elegido, 'FI'))
                    libres.remove(elegido)
            if 'VB' not in asignados and len(libres) > 10 and self.rng.random() < 0.3:
                elegido = self.rng.choice(libres)
                asignados['VB'] = elegido
                self.roles.append((codigo, elegido, 'VB'))

        # Tercer usuario de HR, del grupo de Recursos Humanos. Los usuarios de HR
        # generados tienen una fila en cada grupo, como en producción.
        firmantes_rrhh = set(self.firmantes[GRUPO_RRHH].values())
        tercero = self.rng.choice([e.pernr for e in self.empleados
                                   if e.grupo == GRUPO_RRHH and e.pernr not in prueba | firmantes_rrhh])
        self.hr.append(tercero)
        self.roles += [(codigo, tercero, 'HR') for codigo, *_ in GRUPOS]

    def _dar_de_baja(self):
        """Una parte de la plantilla ya no está en la empresa: dejan de tener partes en
        una fecha aleatoria. Nunca son usuarios de prueba ni tienen roles."""
        con_rol = {pernr for _, pernr, _ in self.roles}
        candidatos = [e for e in self.empleados if e.pernr not in con_rol and int(e.pernr) > len(USUARIOS_PRUEBA)]
        dias_rango = (self.hasta - self.desde).days
        for empleado in self.rng.sample(candidatos, round(len(self.empleados) * PROPORCION_INACTIVOS)):
            empleado.activo = False
            empleado.baja_desde = self.desde + timedelta(days=self.rng.randrange(dias_rango // 4, dias_rango))

    # --- Escritura ---------------------------------------------------------------------

    def _limpiar(self, cursor):
        # Orden: primero las tablas que referencian a otras (la BD de tests tiene claves ajenas)
        for tabla in ('zparte', 'zgrroles', 'userpayroll', 'zperiodos',
                      'grupospayroll', 'departmentspayroll', 'areaspayroll'):
            cursor.execute(f'DELETE FROM `{tabla}`')

    def _catalogos(self, cursor):
        cursor.executemany('INSERT INTO areaspayroll (CODE, NAME) VALUES (%s, %s)', AREAS)
        cursor.executemany(
            'INSERT INTO departmentspayroll (CODE, NAME, DESCRIPTION, ACTIVE) VALUES (%s, %s, %s, 1)',
            [(codigo, nombre, f'Departamento de {nombre}') for codigo, nombre, _ in DEPARTAMENTOS],
        )
        cursor.executemany(
            'INSERT INTO grupospayroll (CODE, EXTERNALCODE, NAME) VALUES (%s, %s, %s)',
            [(codigo, 1000 + codigo, nombre) for codigo, nombre, *_ in GRUPOS],
        )
        # Estados: solo se añaden los que falten (no se modifican los existentes)
        cursor.executemany(
            'INSERT IGNORE INTO eppartstatus (STATUS, DESCRIPTION, COLOR) VALUES (%s, %s, %s)', ESTADOS)

    def _insertar_empleados_y_roles(self, cursor):
        hash_password = AuthService.hashear_password(PASSWORD_PRUEBA)
        cursor.executemany(
            'INSERT INTO userpayroll (NUMPER, NAME, SURNAME, PASSWORD, EMAIL, ACTIVE, DEPARTMENT, AREA, GRUPO, IS_SYNCHRONIZED) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)',
            [
                (e.pernr, e.nombre, e.apellidos, hash_password, e.email, int(e.activo),
                 self.grupos[e.grupo][1], self.departamentos[self.grupos[e.grupo][1]][1], e.grupo)
                for e in self.empleados
            ],
        )
        cursor.executemany('INSERT INTO zgrroles (CODGR, PERNR, ROLNAME) VALUES (%s, %s, %s)', self.roles)

    def _periodos(self, cursor):
        filas = []
        ultimo = periodo_de(self.hasta)
        for anio in range(self.desde.year, int(ultimo[1]) + 1):
            for mes in range(1, 13):
                if (str(anio), f'{mes:02d}') > (ultimo[1], ultimo[0]):
                    break
                inicio, fin = limites_periodo(mes, anio)
                filas.append((
                    f'{mes:02d}', str(anio), f'{NOMBRES_MES[mes - 1]} {anio}', inicio, fin,
                    fin + timedelta(days=5), fin + timedelta(days=10), 'S' if fin < self.hasta else '',
                ))
        cursor.executemany(
            'INSERT INTO zperiodos (ID, EJERCICIO, DESCRIPTION, FECHAINI, FECHAFIN, FEVBUFIN, FEFIRFIN, TRASPASO) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', filas)

    # --- Partes --------------------------------------------------------------------

    def _dias_candidatos(self, empleado):
        """Días en los que el empleado podría tener parte (antes de aplicar la probabilidad)."""
        turnos = self.grupos[empleado.grupo][2]
        fin = min(self.hasta, empleado.baja_desde) if empleado.baja_desde else self.hasta
        ausencias = self._ausencias(empleado)
        dia = self.desde
        while dia <= fin:
            if dia not in ausencias:
                if turnos == 'M':
                    trabaja = tipo_dia(dia) == 'L'
                else:
                    # Turnos: todos los laborables y festivos, y uno de cada dos fines de semana
                    semana = dia.isocalendar()[1]
                    trabaja = dia.weekday() < 5 or (semana + empleado.desfase_turno) % 2 == 0
                if trabaja:
                    yield dia
            dia += timedelta(days=1)

    def _ausencias(self, empleado):
        """Vacaciones (unos 30 días naturales al año, sobre todo en verano) y bajas."""
        rng = random.Random(f'{self.semilla}-{empleado.pernr}')
        dias = set()
        for anio in range(self.desde.year, self.hasta.year + 1):
            inicio = date(anio, rng.choice([6, 7, 7, 8, 8, 9]), rng.randrange(1, 20))
            dias.update(inicio + timedelta(days=n) for n in range(30))
            if rng.random() < 0.3:
                baja = date(anio, rng.randrange(1, 13), rng.randrange(1, 28))
                dias.update(baja + timedelta(days=n) for n in range(rng.randrange(3, 21)))
        return dias

    def _crear_partes(self, cursor, resumen):
        candidatos = [(empleado, dia) for empleado in self.empleados for dia in self._dias_candidatos(empleado)]
        probabilidad = min(1.0, self.objetivo_partes / max(len(candidatos), 1))
        huella = hashlib.sha256()
        lote = []
        insert = (f'INSERT INTO zparte ({", ".join(COLUMNAS_PARTE)}) '
                  f'VALUES ({", ".join(["%s"] * len(COLUMNAS_PARTE))})')
        indices_he = [COLUMNAS_PARTE.index(c) for c in COLUMNAS_HE]
        mandt = MANDT_INICIAL
        for empleado, dia in candidatos:
            if self.rng.random() >= probabilidad:
                continue
            mandt += 1
            fila = self._parte(empleado, dia, mandt)
            huella.update(repr(fila).encode())
            lote.append(fila)
            resumen.partes += 1
            resumen.partes_por_ejercicio[dia.year] = resumen.partes_por_ejercicio.get(dia.year, 0) + 1
            resumen.partes_con_he += any(fila[i] for i in indices_he)
            if len(lote) == TAMANO_LOTE:
                cursor.executemany(insert, lote)
                self.conexion.commit()
                lote = []
        if lote:
            cursor.executemany(insert, lote)
        self.conexion.commit()
        resumen.huella = huella.hexdigest()[:16]

    def _turno(self, empleado, dia, turnos):
        """Turno del día. La rotación semanal es sobre todo de mañana (M ~70 %, T ~15 %,
        N ~8 %), con un ~6 % de turnos 'D', como en los partes reales."""
        if turnos == 'M':
            return 'M'
        if self.rng.random() < 0.06:
            return 'D'
        rotacion = ROTACION_TURNOS[turnos]
        semana = dia.isocalendar()[1]
        return rotacion[(semana + empleado.desfase_turno) % len(rotacion)]

    def _horas_extra(self, turno, dia_tipo):
        rng = self.rng
        horas = dict.fromkeys(COLUMNAS_HE, 0)
        if rng.random() < PROBABILIDAD_HE:
            tramo = ('N' if turno == 'N' else 'D') + ('L' if dia_tipo == 'L' else 'F')
            sufijos = list(TIPOS_HE)
            for _ in range(2 if rng.random() < 0.15 else 1):
                sufijo = rng.choices(sufijos, weights=[TIPOS_HE[s][0] for s in sufijos])[0]
                _, valores, pesos = TIPOS_HE[sufijo]
                if tramo.endswith('F') and sufijo in ('', 'C', 'CO'):
                    valores, pesos = VALORES_FESTIVO
                horas[f'{tramo}{sufijo}'] += rng.choices(valores, weights=pesos)[0]
        if rng.random() < PROBABILIDAD_LLAMADA:
            tramo = ('N' if turno == 'N' else 'D') + ('L' if dia_tipo == 'L' else 'F')
            horas[f'LL{tramo}'] += rng.choices(*VALORES_LLAMADA)[0]
        return horas

    def _parte(self, empleado, dia, mandt):
        rng = self.rng
        _, dpto, turnos = self.grupos[empleado.grupo]
        turno = self._turno(empleado, dia, turnos)
        dia_tipo = tipo_dia(dia)
        mes, ejercicio = periodo_de(dia)
        estado, fechas = self._estado_y_firmas(empleado, dia, mes, ejercicio)
        # Las columnas de teletrabajo/descanso no se rellenaban en los partes antiguos (NULL)
        sin_marcas_nuevas = rng.random() < 0.39
        descanso = rng.random() < 0.03

        valores = {
            'MANDT': mandt, 'PERNR': empleado.pernr, 'PADAT': dia, 'TIPO': 'T', 'TURNO': turno,
            'REDAT': fechas['CRDAT'], 'UPDAT': fechas['UPDAT'], 'MODIF': 'S' if rng.random() < 0.028 else None,
            'MES': mes, 'EJERC': ejercicio, 'STAT': estado, 'PAJOB': 'Z' if rng.random() < 0.24 else '',
            'CODGR': empleado.grupo, 'DPTO': self.departamentos[dpto][0], 'CATEG': empleado.categoria,
            'TIPODIA': dia_tipo, 'HN': 0 if descanso else rng.choices((0, 8, 6, 7), weights=(62, 32, 5, 1))[0],
            **self._horas_extra(turno, dia_tipo),
            **{marca: 'X' if rng.random() < probabilidad else None for marca, probabilidad in MARCAS_X.items()},
            'PA': '1' if rng.random() < 0.006 else None, 'KM': 0,
            'TIPOTURNO': 0 if turnos == 'M' else 1,
            'TELETRABAJO': None if sin_marcas_nuevas else ('t' if turnos == 'M' and rng.random() < 0.05 else 'f'),
            'DESCANSO': None if sin_marcas_nuevas else ('t' if descanso else 'f'),
            'USER_ID': fechas['PERNRCR'],
            **{k: v for k, v in fechas.items() if k != 'UPDAT'},
        }
        return tuple(valores[columna] for columna in COLUMNAS_PARTE)

    def _estado_y_firmas(self, empleado, dia, mes, ejercicio):
        """Estado según el periodo de nómina (cerrado, recién cerrado o abierto) y
        firmas coherentes con ese estado."""
        rng = self.rng
        _, fin_periodo = limites_periodo(int(mes), int(ejercicio))
        if fin_periodo + timedelta(days=10) < self.hasta:      # periodo cerrado y traspasado
            estado = rng.choices('GHI', weights=[96, 3, 1])[0]
        elif fin_periodo < self.hasta:                          # cerrado, pendiente de nómina
            estado = rng.choices('EF', weights=[80, 20])[0]
        else:                                                   # periodo en curso
            estado = rng.choices('ABCDE', weights=[25, 15, 30, 10, 20])[0]

        firmantes = self.firmantes[empleado.grupo]
        visto_bueno = firmantes.get('VB', firmantes['FI'])
        limite = self.hasta

        def despues(fecha, maximo):
            return min(fecha + timedelta(days=rng.randrange(0, maximo + 1)), limite)

        creado = despues(dia, 2)
        fechas = {
            'PERNRCR': empleado.pernr if estado == 'B' else visto_bueno, 'CRDAT': creado,
            'PERNRVB': None, 'VBDAT': None, 'PERNRFI': None, 'FIDAT': None, 'PERNRHR': None, 'HRDAT': None,
        }
        ultima = creado
        if estado in 'CDEFGHI':
            ultima = fechas['VBDAT'] = despues(ultima, 5)
            fechas['PERNRVB'] = visto_bueno
        if estado in 'EFGHI':
            ultima = fechas['FIDAT'] = despues(ultima, 7)
            fechas['PERNRFI'] = firmantes['FI']
        if estado in 'GHI':
            ultima = fechas['HRDAT'] = despues(ultima, 10)
            fechas['PERNRHR'] = rng.choice(self.hr)
        fechas['UPDAT'] = ultima
        return estado, fechas


def conectar():
    """Conexión PyMySQL a la BD del .env."""
    import pymysql
    from config import Config

    return pymysql.connect(
        host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER,
        password=Config.DB_PASSWORD or '', database=Config.DB_NAME,
        charset='utf8mb4', autocommit=False,
    )


def imprimir_resumen(resumen, base_datos):
    print(f'Datos generados en {base_datos} ({resumen.segundos:.1f} s):')
    print(f'  empleados: {resumen.empleados} ({resumen.inactivos} inactivos) en {resumen.grupos} grupos')
    print(f'  filas en zgrroles: {resumen.roles}')
    print(f'  partes: {resumen.partes} ({resumen.partes_con_he} con horas extra), '
          f'del {resumen.desde} al {resumen.hasta}')
    for anio, total in sorted(resumen.partes_por_ejercicio.items()):
        print(f'    {anio}: {total}')
    print(f'  huella (misma semilla y fecha => misma huella): {resumen.huella}')
    print(f'  contraseña de todos los usuarios: {PASSWORD_PRUEBA}')


def main(argumentos=None):
    from config import Config

    parser = argparse.ArgumentParser(description='Genera datos ficticios de demostración (sustituye los actuales).')
    parser.add_argument('--partes', type=int, default=PARTES_POR_DEFECTO, help='número aproximado de partes')
    parser.add_argument('--semilla', type=int, default=SEMILLA_POR_DEFECTO, help='semilla aleatoria')
    parser.add_argument('--hasta', type=date.fromisoformat, default=date.today(), help='fecha final (AAAA-MM-DD)')
    args = parser.parse_args(argumentos)

    if 'prod' in Config.DB_NAME.lower():
        sys.exit(f'Me niego a sustituir los datos de "{Config.DB_NAME}": parece una BD de producción.')

    print(f'Se van a SUSTITUIR los datos de {Config.DB_NAME} en {Config.DB_HOST}:{Config.DB_PORT} '
          f'(partes, empleados, grupos, roles y periodos).')
    conexion = conectar()
    try:
        resumen = GeneradorDatos(conexion, partes=args.partes, semilla=args.semilla, hasta=args.hasta).generar()
    finally:
        conexion.close()
    imprimir_resumen(resumen, Config.DB_NAME)
    return resumen


if __name__ == '__main__':
    main()

"""Carga usuarios y roles de prueba con contraseñas bcrypt.

Uso (desde dashboard_rrhh/, con el venv activo y la BD levantada):
    python seed.py

Es idempotente: se puede ejecutar varias veces. No sobrescribe datos que ya
existan salvo la contraseña de los usuarios de prueba y sus filas de zgrroles.
Los tests reutilizan cargar_datos_prueba() sobre la BD epartes_test.
"""
from datetime import date

from extensions import db
from models import AreasPayroll, DepartmentPayroll, EppartStatus, GruposPayroll, UserPayroll, ZgrRoles, ZParte
from services.auth_service import AuthService

PASSWORD_PRUEBA = 'Tirme2026!'

# Catálogos mínimos (los mismos que trae el dump)
GRUPOS = [(1, 1001, 'Grupo Técnico A'), (2, 1002, 'Grupo Operativo B')]
AREAS = [(100, 'Desarrollo Software'), (200, 'Mantenimiento y Planta')]
DEPARTAMENTOS = [(10, 'Sistemas e IT'), (20, 'Operaciones')]

# Usuarios de prueba: (NUMPER, nombre, apellidos, email, grupo, área, departamento,
# filas de zgrroles como (ROLNAME, CODGR))
USUARIOS = [
    ('00000001', 'Juan', 'Pérez Gómez', 'jperez@empresa.local', 1, 100, 10, []),
    ('00000002', 'María', 'García López', 'mgarcia@empresa.local', 1, 100, 10, [('VB', 1)]),
    ('00000003', 'Carlos', 'Rodríguez Silva', 'crodriguez@empresa.local', 2, 200, 20, [('FI', 2)]),
    ('00000004', 'Ana', 'Torres Vidal', 'atorres@empresa.local', 1, 100, 10, [('HR', 1)]),
    ('00000005', 'Elena', 'Ruiz Martín', 'eruiz@empresa.local', 2, 200, 20, [('HR', 2), ('VB', 2)]),
]

# Partes: (MANDT, PERNR, PADAT, TURNO, CODGR, DPTO). Los tres primeros son los
# del dump; el último es de María (VB del grupo 1) en el grupo 2, para comprobar
# que un mando ve también sus propios partes fuera de sus grupos.
PARTES = [
    (1786358400000, '00000001', date(2026, 8, 10), 'M', 1, 'Sistemas e IT'),
    (1786358400001, '00000003', date(2026, 8, 10), 'T', 2, 'Operaciones'),
    (1786444800000, '00000001', date(2026, 8, 11), 'M', 1, 'Sistemas e IT'),
    (1786531200000, '00000002', date(2026, 8, 12), 'M', 2, 'Operaciones'),
]


def _crear_si_no_existe(session, modelo, clave, **campos):
    if session.get(modelo, clave) is None:
        session.add(modelo(**campos))


# Estados de eppartstatus (los mismos que en producción)
ESTADOS = [
    ('A', 'Creado por el encargado', '#FF8040'),
    ('B', 'Creado por el empleado', '#FF0000'),
    ('C', 'Visto bueno por el jefe de área', '#00FF00'),
    ('D', 'Modificado y visto bueno por el jefe de área', '#FF0080'),
    ('E', 'Firmado por el jefe de departamento', '#299999'),
    ('F', 'Modificado y firmado por el jefe de departamento.', '#800080'),
    ('G', 'Traspasado a nómina por RRHH', '#00FFFF'),
    ('H', 'Modificado por RRHH', '#666699'),
    ('I', 'Modificado por RRHH y traspasado a nómina por RRHH', '#0000FF'),
]


def cargar_datos_prueba(session):
    """Inserta o actualiza los datos de prueba en la BD de la sesión dada."""
    for estado, descripcion, color in ESTADOS:
        _crear_si_no_existe(session, EppartStatus, estado, STATUS=estado, DESCRIPTION=descripcion, COLOR=color)
    for code, externo, nombre in GRUPOS:
        _crear_si_no_existe(session, GruposPayroll, code, CODE=code, EXTERNALCODE=externo, NAME=nombre)
    for code, nombre in AREAS:
        _crear_si_no_existe(session, AreasPayroll, code, CODE=code, NAME=nombre)
    for code, nombre in DEPARTAMENTOS:
        _crear_si_no_existe(session, DepartmentPayroll, code, CODE=code, NAME=nombre)
    session.flush()

    # Los roles EM/JA del dump no son perfiles de este dashboard
    session.execute(db.delete(ZgrRoles).where(ZgrRoles.ROLNAME.in_(['EM', 'JA'])))

    hash_prueba = AuthService.hashear_password(PASSWORD_PRUEBA)
    for numper, nombre, apellidos, email, grupo, area, dpto, roles in USUARIOS:
        usuario = session.scalar(db.select(UserPayroll).where(UserPayroll.NUMPER == numper))
        if usuario is None:
            usuario = UserPayroll(
                NUMPER=numper, NAME=nombre, SURNAME=apellidos, EMAIL=email,
                ACTIVE=True, GRUPO=grupo, AREA=area, DEPARTMENT=dpto,
            )
            session.add(usuario)
        usuario.PASSWORD = hash_prueba

        # Deja exactamente los roles definidos arriba para este usuario
        session.execute(db.delete(ZgrRoles).where(ZgrRoles.PERNR == numper))
        for rolname, codgr in roles:
            session.add(ZgrRoles(CODGR=codgr, PERNR=numper, ROLNAME=rolname))

    for mandt, pernr, padat, turno, codgr, dpto in PARTES:
        _crear_si_no_existe(
            session, ZParte, (mandt, pernr, padat, 'N', turno),
            MANDT=mandt, PERNR=pernr, PADAT=padat, TIPO='N', TURNO=turno,
            MES=f'{padat.month:02d}', EJERC=str(padat.year), CODGR=codgr, DPTO=dpto,
        )

    session.commit()


if __name__ == '__main__':
    from app import app

    with app.app_context():
        cargar_datos_prueba(db.session)
        print(f'Datos de prueba cargados en {app.config["SQLALCHEMY_DATABASE_URI"].database}.')
        print(f'Contraseña de todos los usuarios de prueba: {PASSWORD_PRUEBA}')
        for numper, nombre, _, email, _, _, _, roles in USUARIOS:
            perfiles = ', '.join(f'{r} grupo {g}' for r, g in roles) or 'sin rol (empleado)'
            print(f'  {email:28} {perfiles}')

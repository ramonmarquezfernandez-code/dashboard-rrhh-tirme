"""Resumen de la plantilla activa (userpayroll)."""
from sqlalchemy import func

from extensions import db
from models import AreasPayroll, DepartmentPayroll, GruposPayroll, UserPayroll

# Valores del combo del frontend que significan "sin filtro"
SIN_FILTRO_GRUPO = 'TODOS'
SIN_FILTRO_DIRECCION = 'TODAS'


class PlantillaService:
    """Recuentos de empleados activos limitados por el filtro de perfil."""

    def __init__(self, filtro_plantilla):
        self.filtro_plantilla = filtro_plantilla

    def _filtros(self, grupo, direccion):
        filtros = [UserPayroll.ACTIVE == True, self.filtro_plantilla]  # noqa: E712
        if grupo and grupo.upper() != SIN_FILTRO_GRUPO:
            filtros.append(GruposPayroll.NAME == grupo)
        if direccion and direccion.upper() != SIN_FILTRO_DIRECCION:
            filtros.append(AreasPayroll.NAME == direccion)
        return filtros

    @staticmethod
    def _base(*columnas):
        """Consulta sobre userpayroll con los joins que usan los filtros de grupo y área."""
        return (db.session.query(*columnas).select_from(UserPayroll)
                .outerjoin(GruposPayroll, UserPayroll.GRUPO == GruposPayroll.CODE)
                .outerjoin(AreasPayroll, UserPayroll.AREA == AreasPayroll.CODE))

    def _desglose(self, filtros, columna, sin_valor):
        """Empleados agrupados por el nombre de grupo, área o departamento."""
        consulta = self._base(
            func.coalesce(columna, sin_valor).label('nombre'),
            func.count(UserPayroll.ID).label('total'),
        )
        if columna is DepartmentPayroll.NAME:
            consulta = consulta.outerjoin(DepartmentPayroll, UserPayroll.DEPARTMENT == DepartmentPayroll.CODE)
        filas = (consulta.filter(*filtros).group_by(columna)
                 .order_by(func.count(UserPayroll.ID).desc()).all())
        return [{'nombre': fila.nombre, 'total': int(fila.total)} for fila in filas]

    def opciones(self):
        """Grupos y áreas con empleados visibles para el perfil (para los combos de filtro)."""
        filtros = self._filtros('', '')

        def nombres(columna):
            filas = (self._base(columna).filter(*filtros, columna.isnot(None))
                     .distinct().order_by(columna.asc()).all())
            return [fila[0] for fila in filas]

        return {'grupos': nombres(GruposPayroll.NAME), 'areas': nombres(AreasPayroll.NAME)}

    def resumen(self, grupo='', direccion=''):
        filtros = self._filtros(grupo, direccion)
        total = self._base(func.count(UserPayroll.ID)).filter(*filtros).scalar() or 0
        return {
            'total_plantilla': int(total),
            'por_grupo': self._desglose(filtros, GruposPayroll.NAME, 'Sin grupo'),
            'por_area': self._desglose(filtros, AreasPayroll.NAME, 'Sin área'),
            'por_departamento': self._desglose(filtros, DepartmentPayroll.NAME, 'Sin departamento'),
            **self.opciones(),
        }

    def listado(self, grupo='', direccion=''):
        """Directorio de empleados activos. Solo columnas de una lista blanca:
        nunca se devuelven contraseñas, tokens, UUID ni documento de identidad."""
        filas = (self._base(
            UserPayroll.NUMPER.label('pernr'),
            UserPayroll.NAME.label('nombre'),
            UserPayroll.SURNAME.label('apellidos'),
            UserPayroll.EMAIL.label('email'),
            GruposPayroll.NAME.label('grupo'),
            AreasPayroll.NAME.label('area'),
            DepartmentPayroll.NAME.label('departamento'),
        ).outerjoin(DepartmentPayroll, UserPayroll.DEPARTMENT == DepartmentPayroll.CODE)
            .filter(*self._filtros(grupo, direccion))
            .order_by(UserPayroll.SURNAME.asc(), UserPayroll.NAME.asc(), UserPayroll.NUMPER.asc())
            .all())
        empleados = [fila._asdict() for fila in filas]
        return {'empleados': empleados, 'total': len(empleados), **self.opciones()}

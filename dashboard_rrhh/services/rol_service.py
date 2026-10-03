from extensions import db
from models import ZgrRoles

# Roles que expone la API, ordenados de mayor a menor prioridad
ROL_HR = 'hr'
ROL_MANDO = 'mando'
ROL_EMPLEADO = 'empleado'
PRIORIDAD_ROLES = (ROL_HR, ROL_MANDO, ROL_EMPLEADO)

# Valores de zgrroles.ROLNAME que dan cada rol
ROLNAMES_HR = {'HR'}
ROLNAMES_MANDO = {'VB', 'FI'}


class RolService:
    """Lee los roles de un trabajador en la tabla zgrroles.

    - ROLNAME 'HR'        -> rol 'hr' (acceso total).
    - ROLNAME 'VB' o 'FI' -> rol 'mando' sobre los grupos (CODGR) de esas filas.
    - Cualquier usuario   -> rol 'empleado' (siempre disponible).
    """

    def __init__(self, pernr):
        self.pernr = pernr
        self._filas = db.session.scalars(
            db.select(ZgrRoles).where(ZgrRoles.PERNR == pernr)
        ).all()

    def _rolnames(self):
        return {(fila.ROLNAME or '').strip().upper() for fila in self._filas}

    def roles_disponibles(self):
        """Roles del usuario ordenados por prioridad (HR > mando > empleado)."""
        rolnames = self._rolnames()
        roles = []
        if rolnames & ROLNAMES_HR:
            roles.append(ROL_HR)
        if rolnames & ROLNAMES_MANDO:
            roles.append(ROL_MANDO)
        roles.append(ROL_EMPLEADO)
        return roles

    def codgrs_mando(self):
        """Grupos (CODGR) en los que el usuario tiene rol VB o FI."""
        return {
            fila.CODGR
            for fila in self._filas
            if (fila.ROLNAME or '').strip().upper() in ROLNAMES_MANDO
        }

    def tiene_rol(self, rol):
        return rol in self.roles_disponibles()

    def rol_por_defecto(self):
        return self.roles_disponibles()[0]

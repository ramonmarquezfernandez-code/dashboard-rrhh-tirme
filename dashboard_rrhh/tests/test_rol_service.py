"""RolService: roles disponibles, prioridad y grupos de mando según zgrroles."""
import pytest

from services.rol_service import RolService


@pytest.mark.parametrize('pernr, roles, codgrs', [
    ('00000001', ['empleado'], set()),               # sin filas en zgrroles
    ('00000002', ['mando', 'empleado'], {1}),         # VB grupo 1
    ('00000003', ['mando', 'empleado'], {2}),         # FI grupo 2
    ('00000004', ['hr', 'empleado'], set()),          # HR
    ('00000005', ['hr', 'mando', 'empleado'], {2}),   # HR + VB grupo 2
    ('99999999', ['empleado'], set()),               # no existe: solo empleado
])
def test_roles_y_grupos(app_bd, pernr, roles, codgrs):
    with app_bd.app_context():
        servicio = RolService(pernr)
        assert servicio.roles_disponibles() == roles
        assert servicio.codgrs_mando() == codgrs
        assert servicio.rol_por_defecto() == roles[0]
        assert servicio.tiene_rol('empleado')

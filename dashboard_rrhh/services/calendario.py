"""Calendario laboral: tipo de día (zparte.TIPODIA) y periodo de nómina (zperiodos)."""
from extensions import db
from models import ZPeriodos

# Festivos fijos nacionales y de Baleares (día, mes). Los festivos locales los
# marca el empleado en el formulario ("festivo local").
FESTIVOS = {(1, 1), (6, 1), (1, 3), (1, 5), (15, 8), (12, 10), (1, 11), (6, 12), (8, 12), (25, 12)}


def tipo_dia(fecha):
    """L laborable, S sábado, D domingo, F festivo (como zparte.TIPODIA)."""
    if (fecha.day, fecha.month) in FESTIVOS:
        return 'F'
    return {5: 'S', 6: 'D'}.get(fecha.weekday(), 'L')


def periodo_de(fecha):
    """Periodo de nómina de zperiodos que contiene la fecha, o None si no hay ninguno."""
    return db.session.scalar(
        db.select(ZPeriodos)
        .where(ZPeriodos.FECHAINI <= fecha, ZPeriodos.FECHAFIN >= fecha)
        .order_by(ZPeriodos.EJERCICIO.desc(), ZPeriodos.ID.desc())
    )


def periodo_traspasado(periodo):
    """True si el periodo ya se ha traspasado a nómina (no admite partes nuevos)."""
    return (periodo.TRASPASO or '').strip().upper() == 'S'

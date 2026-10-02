from extensions import db

class ZPeriodos(db.Model):
    __tablename__ = 'zperiodos'

    ID = db.Column(db.String(2), primary_key=True)
    EJERCICIO = db.Column(db.String(4), primary_key=True)
    DESCRIPTION = db.Column(db.String(255), nullable=True)
    FECHAINI = db.Column(db.Date, nullable=True)
    FECHAFIN = db.Column(db.Date, nullable=True)
    FEVBUFIN = db.Column(db.Date, nullable=True)
    FEFIRFIN = db.Column(db.Date, nullable=True)
    TRASPASO = db.Column(db.String(1), nullable=True)
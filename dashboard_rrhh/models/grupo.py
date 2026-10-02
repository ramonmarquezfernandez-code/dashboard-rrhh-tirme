from extensions import db

class GruposPayroll(db.Model):
    __tablename__ = 'grupospayroll'

    CODE = db.Column(db.Integer, primary_key=True, autoincrement=False)
    EXTERNALCODE = db.Column(db.Integer, nullable=False)
    NAME = db.Column(db.String(100), nullable=True)
    SYNCRONIZED_A3 = db.Column(db.Boolean, default=False)
    SYNCRONIZED_A3_DATE = db.Column(db.Date, nullable=True)
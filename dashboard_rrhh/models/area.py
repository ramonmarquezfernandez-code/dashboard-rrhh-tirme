from extensions import db

class AreasPayroll(db.Model):
    __tablename__ = 'areaspayroll'

    CODE = db.Column(db.Integer, primary_key=True, autoincrement=False)
    NAME = db.Column(db.String(50), nullable=False)
    SYNCRONIZED_A3 = db.Column(db.Boolean, default=False)
    SYNCRONIZED_A3_DATE = db.Column(db.Date, nullable=True)
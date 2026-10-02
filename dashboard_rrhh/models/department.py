from extensions import db

class DepartmentPayroll(db.Model):
    __tablename__ = 'departmentspayroll'

    CODE = db.Column(db.Integer, primary_key=True, autoincrement=False)
    NAME = db.Column(db.String(100), nullable=True)
    DESCRIPTION = db.Column(db.String(100), nullable=True)
    ACTIVE = db.Column(db.Boolean, default=True)
    SYNCRONIZED_A3 = db.Column(db.Boolean, default=False)
    SYNCRONIZED_A3_DATE = db.Column(db.Date, nullable=True)
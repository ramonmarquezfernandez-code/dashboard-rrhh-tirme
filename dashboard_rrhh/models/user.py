from extensions import db

class UserPayroll(db.Model):
    __tablename__ = 'userpayroll'

    ID = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    NUMPER = db.Column(db.String(8), nullable=False, index=True)
    NAME = db.Column(db.String(50), nullable=False)
    SURNAME = db.Column(db.String(50), nullable=True)
    PASSWORD = db.Column(db.String(60), nullable=True)
    PASSWORD1 = db.Column(db.String(60), nullable=True)
    PASSWORD2 = db.Column(db.String(60), nullable=True)
    EMAIL = db.Column(db.String(100), nullable=True)
    NUMHUELLA = db.Column(db.String(8), nullable=True)
    UUID = db.Column(db.LargeBinary(16), nullable=True)
    PW_REFRESH_TOKEN = db.Column(db.String(255), nullable=True)
    TOKEN_EXPIRATION = db.Column(db.String(255), nullable=True)
    ACTIVE = db.Column(db.Boolean, nullable=True)
    DEPARTMENT = db.Column(db.Integer, db.ForeignKey('departmentspayroll.CODE'), nullable=True)
    IDENTIFIER_NUMBER = db.Column(db.String(9), nullable=True)
    AREA = db.Column(db.Integer, db.ForeignKey('areaspayroll.CODE'), nullable=True)
    CLASSIFICATION_ID = db.Column(db.BigInteger, db.ForeignKey('tep_classificationpayroll.ID'), nullable=True)
    ASSIGNED_TURN = db.Column(db.String(250), nullable=True)
    IS_SYNCHRONIZED = db.Column(db.Boolean, default=False)
    SYNCHRONIZED_DATE = db.Column(db.Date, nullable=True)
    GRUPO = db.Column(db.Integer, db.ForeignKey('grupospayroll.CODE'), default=0)
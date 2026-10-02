from extensions import db

class TepClassificationPayroll(db.Model):
    __tablename__ = 'tep_classificationpayroll'

    ID = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    CLASSIFICATION_SUMMARY = db.Column(db.String(20), nullable=False)
    CLASSIFICATION_DESCRIPTION = db.Column(db.String(250), nullable=False)
    IS_SYNCHRONIZED = db.Column(db.Boolean, default=False)
    SYNCHRONIZED_DATE = db.Column(db.Date, nullable=True)
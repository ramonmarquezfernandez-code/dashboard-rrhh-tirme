from extensions import db

class EppartStatus(db.Model):
    __tablename__ = 'eppartstatus'

    STATUS = db.Column(db.String(1), primary_key=True)
    DESCRIPTION = db.Column(db.String(100), nullable=False)
    COLOR = db.Column(db.String(7), nullable=False)
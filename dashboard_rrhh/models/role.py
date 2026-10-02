from extensions import db

class ZgrRoles(db.Model):
    __tablename__ = 'zgrroles'

    CODGR = db.Column(db.Integer, primary_key=True)
    PERNR = db.Column(db.String(8), primary_key=True)
    ROLNAME = db.Column(db.String(2), primary_key=True)
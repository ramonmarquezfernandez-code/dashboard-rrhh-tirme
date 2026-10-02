from extensions import ma
from models import ZParte

class ZParteSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ZParte
        load_instance = True

parte_schema = ZParteSchema()
partes_schema = ZParteSchema(many=True)
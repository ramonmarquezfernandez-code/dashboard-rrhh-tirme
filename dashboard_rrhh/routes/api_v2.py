from flask_restx import Api, Resource, fields, Namespace
from sqlalchemy import func
from extensions import db
from models import UserPayroll, ZParte

# Crear un namespace para los partes
partes_ns = Namespace('partes', description='Operaciones con partes de horas')

# Modelos para documentación Swagger
parte_model = partes_ns.model(
    'Parte',
    {
        'MANDT': fields.Integer(description='Cliente'),
        'PERNR': fields.String(description='Número de personal'),
        'PADAT': fields.Date(description='Fecha del parte'),
        'TIPO': fields.String(description='Tipo de parte'),
        'TURNO': fields.String(description='Turno'),
        'DPTO': fields.String(description='Departamento'),
        'HN': fields.Integer(description='Horas normales'),
        'HP': fields.Integer(description='Horas parciales'),
        'DL': fields.Integer(description='Diurnas libres'),
        'DF': fields.Integer(description='Diurnas festivas'),
        'STAT': fields.String(description='Estado del parte'),
    }
)

resumen_departamento_model = partes_ns.model(
    'ResumenDepartamento',
    {
        'departamento': fields.String(description='Nombre del departamento'),
        'normales': fields.Integer(description='Horas extras normales'),
        'compensar': fields.Integer(description='Horas extras para compensar'),
        'busca': fields.Integer(description='Horas extras en busca'),
        'buscanp': fields.Integer(description='Horas extras en busca sin pago'),
        'combo': fields.Integer(description='Horas extras combo'),
        'total': fields.Integer(description='Total de horas extras'),
    }
)

resumen_trabajador_model = partes_ns.model(
    'ResumenTrabajador',
    {
        'id': fields.String(description='Número de personal'),
        'trabajador': fields.String(description='Nombre del trabajador'),
        'normales': fields.Integer(description='Horas extras normales'),
        'compensar': fields.Integer(description='Horas extras para compensar'),
        'busca': fields.Integer(description='Horas extras en busca'),
        'buscanp': fields.Integer(description='Horas extras en busca sin pago'),
        'combo': fields.Integer(description='Horas extras combo'),
        'total': fields.Integer(description='Total de horas extras'),
        'totalretrib': fields.Integer(description='Total retribuible'),
    }
)


def get_he_expressions():
    """Calcula las expresiones de horas extras sobre campos de MariaDB"""
    he_normales = ZParte.DL + ZParte.DF + ZParte.NL + ZParte.NF
    he_compensar = ZParte.DLC + ZParte.DFC + ZParte.NLC + ZParte.NFC
    he_busca = ZParte.DLB + ZParte.DFB + ZParte.NLB + ZParte.NFB
    he_buscanp = ZParte.DLBN + ZParte.DFBN + ZParte.NLBN + ZParte.NFBN
    he_combo = ZParte.DLCO + ZParte.DFCO + ZParte.NLCO + ZParte.NFCO
    total_he = he_normales + he_compensar + he_busca + he_buscanp + he_combo
    return he_normales, he_compensar, he_busca, he_buscanp, he_combo, total_he


@partes_ns.route('')
class PartesListado(Resource):
    @partes_ns.doc('list_partes', params={'page': 'Número de página', 'per_page': 'Resultados por página'})
    @partes_ns.marshal_list_with(parte_model)
    def get(self):
        """
        Obtiene el listado paginado de partes de horas
        """
        from flask import request

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        pagination = ZParte.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        return pagination.items


@partes_ns.route('/empleado/<string:pernr>')
class PartesEmpleado(Resource):
    @partes_ns.doc('get_partes_empleado')
    @partes_ns.marshal_list_with(parte_model)
    def get(self, pernr):
        """
        Obtiene los partes de horas de un empleado específico
        """
        partes = ZParte.query.filter_by(PERNR=pernr).all()
        if not partes:
            partes_ns.abort(
                404, f'No se encontraron partes para el empleado {pernr}'
            )
        return partes


@partes_ns.route('/resumen-departamento')
class ResumenDepartamento(Resource):
    @partes_ns.doc(
        'get_resumen_departamento', params={'anio': 'Año de ejercicio (ej: 2026)'}
    )
    @partes_ns.marshal_list_with(resumen_departamento_model)
    def get(self):
        """
        Obtiene un resumen de horas extras agrupado por departamento
        """
        from flask import request

        anio = request.args.get('anio', '2026', type=str)
        norm, comp, busca, buscanp, combo, total = get_he_expressions()

        query = db.session.query(
            ZParte.DPTO.label('departamento'),
            func.coalesce(func.sum(norm), 0).label('normales'),
            func.coalesce(func.sum(comp), 0).label('compensar'),
            func.coalesce(func.sum(busca), 0).label('busca'),
            func.coalesce(func.sum(buscanp), 0).label('buscanp'),
            func.coalesce(func.sum(combo), 0).label('combo'),
            func.coalesce(func.sum(total), 0).label('total'),
        ).filter(ZParte.EJERC == anio).group_by(ZParte.DPTO).all()

        return [row._asdict() for row in query]


@partes_ns.route('/resumen-trabajador')
class ResumenTrabajador(Resource):
    @partes_ns.doc(
        'get_resumen_trabajador', params={'anio': 'Año de ejercicio (ej: 2026)'}
    )
    @partes_ns.marshal_list_with(resumen_trabajador_model)
    def get(self):
        """
        Obtiene un resumen de horas extras agrupado por trabajador
        """
        from flask import request

        anio = request.args.get('anio', '2026', type=str)
        norm, comp, busca, buscanp, combo, total = get_he_expressions()

        query = db.session.query(
            UserPayroll.NAME.label('trabajador'),
            ZParte.PERNR.label('id'),
            func.coalesce(func.sum(norm), 0).label('normales'),
            func.coalesce(func.sum(comp), 0).label('compensar'),
            func.coalesce(func.sum(busca), 0).label('busca'),
            func.coalesce(func.sum(buscanp), 0).label('buscanp'),
            func.coalesce(func.sum(combo), 0).label('combo'),
            func.coalesce(func.sum(total), 0).label('total'),
            func.coalesce(func.sum(norm + busca), 0).label('totalretrib'),
        ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER).filter(
            ZParte.EJERC == anio
        ).group_by(ZParte.PERNR, UserPayroll.NAME).all()

        return [row._asdict() for row in query]


@partes_ns.route('/comite')
class HeComite(Resource):
    @partes_ns.doc(
        'get_he_comite', params={'anio': 'Año de ejercicio (ej: 2026)'}
    )
    def get(self):
        """
        Obtiene el resumen de horas extras para el comité
        """
        from flask import request, jsonify

        anio = request.args.get('anio', '2026', type=str)
        _, _, _, _, _, total = get_he_expressions()

        query = db.session.query(
            ZParte.PERNR.label('id_empleado'),
            func.coalesce(func.sum(total), 0).label('horas_extras'),
        ).filter(ZParte.EJERC == anio).group_by(ZParte.PERNR).all()

        return jsonify([row._asdict() for row in query])

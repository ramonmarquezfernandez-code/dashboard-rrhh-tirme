import calendar
from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy import extract, func

from extensions import db
from models import AreasPayroll, DepartmentPayroll, EppartStatus, GruposPayroll, UserPayroll, ZParte, ZPeriodos
from schemas.parte_schema import partes_schema

partes_bp = Blueprint('partes', __name__, url_prefix='/api/partes')


# ---------------------------------------------------------
# ESTADOS DE PARTES (tabla eppartstatus)
# ---------------------------------------------------------

@partes_bp.route('/estados', methods=['GET'])
def get_estados():
    """Devuelve los estados de parte disponibles en la tabla eppartstatus,
    usados para poblar los combos de filtro 'Estado' de las distintas pantallas."""
    estados = EppartStatus.query.order_by(EppartStatus.STATUS).all()
    return jsonify([
        {'valor': estado.STATUS, 'etiqueta': estado.DESCRIPTION, 'color': estado.COLOR}
        for estado in estados
    ]), 200

# Fórmulas base de horas extras sobre campos de MariaDB
def get_he_expressions():
    he_normales = ZParte.DL + ZParte.DF + ZParte.NL + ZParte.NF
    he_compensar = ZParte.DLC + ZParte.DFC + ZParte.NLC + ZParte.NFC
    he_busca = ZParte.DLB + ZParte.DFB + ZParte.NLB + ZParte.NFB
    he_buscanp = ZParte.DLBN + ZParte.DFBN + ZParte.NLBN + ZParte.NFBN
    he_combo = ZParte.DLCO + ZParte.DFCO + ZParte.NLCO + ZParte.NFCO
    total_he = he_normales + he_compensar + he_busca + he_buscanp + he_combo
    return he_normales, he_compensar, he_busca, he_buscanp, he_combo, total_he


@partes_bp.route('/he-por-periodo', methods=['GET'])
def get_he_por_periodo():
    anio = request.args.get('anio', '2026', type=str)
    mes_desde = max(request.args.get('mes_desde', 1, type=int), 1)
    mes_hasta = min(request.args.get('mes_hasta', 12, type=int), 12)
    anio_natural = request.args.get('anio_natural', 'false').lower() in {'true', '1', 'si', 'yes'}
    departamento = request.args.get('departamento', '').strip()
    pernr = request.args.get('pernr', '').strip()
    estado = request.args.get('estado', '').strip()
    periodo_id = request.args.get('periodo_id', '').strip()

    if mes_desde > mes_hasta:
        return jsonify({'message': 'El periodo de meses no es válido.'}), 400

    periodos = ZPeriodos.query.filter_by(EJERCICIO=anio).order_by(ZPeriodos.ID).all()
    periodo_seleccionado = next((periodo for periodo in periodos if periodo.ID == periodo_id), None)
    if periodo_id and not anio_natural and not periodo_seleccionado:
        return jsonify({'message': 'El periodo seleccionado no existe para el ejercicio indicado.'}), 400

    if periodo_seleccionado and not anio_natural:
        meses = [periodo_seleccionado.ID]
    else:
        meses = [f'{mes:02d}' for mes in range(mes_desde, mes_hasta + 1)]
    norm, comp, busca, buscanp, combo, total = get_he_expressions()
    if anio_natural:
        fecha_desde = date(int(anio), mes_desde, 1)
        ultimo_dia = calendar.monthrange(int(anio), mes_hasta)[1]
        fecha_hasta = date(int(anio), mes_hasta, ultimo_dia)
        filtros_periodo = [ZParte.PADAT.between(fecha_desde, fecha_hasta)]
        mes_consulta = func.month(ZParte.PADAT)
    else:
        ejercicio_periodo = periodo_seleccionado.EJERCICIO if periodo_seleccionado else anio
        filtros_periodo = [ZParte.EJERC == ejercicio_periodo, ZParte.MES.in_(meses)]
        mes_consulta = ZParte.MES

    if departamento:
        filtros_periodo.append(ZParte.DPTO == departamento)
    if pernr:
        filtros_periodo.append(ZParte.PERNR == pernr)
    if estado:
        filtros_periodo.append(ZParte.STAT == estado)

    mensual_query = db.session.query(
        mes_consulta.label('mes'),
        func.coalesce(func.sum(norm), 0).label('normales'),
        func.coalesce(func.sum(comp), 0).label('compensar'),
        func.coalesce(func.sum(busca), 0).label('busca'),
        func.coalesce(func.sum(buscanp), 0).label('buscanp'),
        func.coalesce(func.sum(combo), 0).label('combo'),
        func.coalesce(func.sum(total), 0).label('total'),
    ).filter(*filtros_periodo).group_by(mes_consulta).all()

    mensual_por_mes = {str(row.mes).zfill(2): row._asdict() for row in mensual_query}
    mensual = [
        mensual_por_mes.get(
            mes,
            {
                'mes': mes,
                'normales': 0,
                'compensar': 0,
                'busca': 0,
                'buscanp': 0,
                'combo': 0,
                'total': 0,
            },
        )
        for mes in meses
    ]

    departamentos = db.session.query(
        ZParte.DPTO.label('departamento'),
        func.coalesce(func.sum(norm), 0).label('normales'),
        func.coalesce(func.sum(comp), 0).label('compensar'),
        func.coalesce(func.sum(busca), 0).label('busca'),
        func.coalesce(func.sum(buscanp), 0).label('buscanp'),
        func.coalesce(func.sum(combo), 0).label('combo'),
        func.coalesce(func.sum(total), 0).label('total'),
    ).filter(*filtros_periodo).group_by(ZParte.DPTO).order_by(func.sum(total).desc()).all()

    trabajadores = db.session.query(
        UserPayroll.NAME.label('nombre'),
        UserPayroll.SURNAME.label('apellidos'),
        ZParte.PERNR.label('id'),
        ZParte.DPTO.label('departamento'),
        func.coalesce(func.sum(norm), 0).label('normales'),
        func.coalesce(func.sum(comp), 0).label('compensar'),
        func.coalesce(func.sum(busca), 0).label('busca'),
        func.coalesce(func.sum(buscanp), 0).label('buscanp'),
        func.coalesce(func.sum(combo), 0).label('combo'),
        func.coalesce(func.sum(total), 0).label('total'),
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER) \
     .filter(*filtros_periodo) \
     .group_by(ZParte.PERNR, UserPayroll.NAME, UserPayroll.SURNAME, ZParte.DPTO) \
     .order_by(func.sum(total).desc()).all()

    return jsonify({
        'anio': anio,
        'anio_natural': anio_natural,
        'periodo_id': periodo_id,
        'mes_desde': mes_desde,
        'mes_hasta': mes_hasta,
        'periodos': [
            {
                'id': periodo.ID,
                'ejercicio': periodo.EJERCICIO,
                'descripcion': periodo.DESCRIPTION or f'Periodo {periodo.ID}',
                'fecha_inicio': periodo.FECHAINI.isoformat() if periodo.FECHAINI else None,
                'fecha_fin': periodo.FECHAFIN.isoformat() if periodo.FECHAFIN else None,
            }
            for periodo in periodos
        ],
        'mensual': mensual,
        'departamentos': [row._asdict() for row in departamentos],
        'trabajadores': [row._asdict() for row in trabajadores],
    }), 200


@partes_bp.route('/he-por-empleado', methods=['GET'])
def get_he_por_empleado():
    anio = request.args.get('anio', '2026', type=str)
    mes_desde = max(request.args.get('mes_desde', 1, type=int), 1)
    mes_hasta = min(request.args.get('mes_hasta', 12, type=int), 12)
    anio_natural = request.args.get('anio_natural', 'false').lower() in {'true', '1', 'si', 'yes'}
    departamento = request.args.get('departamento', '').strip()
    pernr = request.args.get('pernr', '').strip()
    estado = request.args.get('estado', '').strip()
    periodo_id = request.args.get('periodo_id', '').strip()
    orden = request.args.get('orden', 'horas').lower()

    if mes_desde > mes_hasta:
        return jsonify({'message': 'El periodo de meses no es válido.'}), 400

    periodos = ZPeriodos.query.filter_by(EJERCICIO=anio).order_by(ZPeriodos.ID).all()
    periodo_seleccionado = next((periodo for periodo in periodos if periodo.ID == periodo_id), None)
    if periodo_id and not anio_natural and not periodo_seleccionado:
        return jsonify({'message': 'El periodo seleccionado no existe para el ejercicio indicado.'}), 400

    if anio_natural:
        fecha_desde = date(int(anio), mes_desde, 1)
        fecha_hasta = date(int(anio), mes_hasta, calendar.monthrange(int(anio), mes_hasta)[1])
        filtros = [ZParte.PADAT.between(fecha_desde, fecha_hasta)]
    elif periodo_seleccionado:
        filtros = [ZParte.EJERC == periodo_seleccionado.EJERCICIO, ZParte.MES == periodo_seleccionado.ID]
    else:
        filtros = [ZParte.EJERC == anio, ZParte.MES.in_([f'{mes:02d}' for mes in range(mes_desde, mes_hasta + 1)])]

    if departamento:
        filtros.append(ZParte.DPTO == departamento)
    if pernr:
        filtros.append(ZParte.PERNR == pernr)
    if estado:
        filtros.append(ZParte.STAT == estado)

    _, _, _, _, _, total_he = get_he_expressions()
    horas = func.coalesce(func.sum(total_he), 0)
    query = db.session.query(
        ZParte.PERNR.label('pernr'),
        UserPayroll.NAME.label('nombre'),
        UserPayroll.SURNAME.label('apellidos'),
        func.coalesce(func.sum(total_he), 0).label('horas_extra'),
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER) \
     .filter(*filtros) \
     .group_by(ZParte.PERNR, UserPayroll.NAME, UserPayroll.SURNAME)

    if orden == 'pernr':
        query = query.order_by(ZParte.PERNR.asc())
    else:
        query = query.order_by(horas.desc(), ZParte.PERNR.asc())

    empleados = query.all()
    total = sum(int(row.horas_extra or 0) for row in empleados)
    departamentos = [
        row[0]
        for row in db.session.query(ZParte.DPTO)
        .filter(*filtros)
        .filter(ZParte.DPTO.isnot(None))
        .distinct()
        .order_by(ZParte.DPTO.asc())
        .all()
    ]

    return jsonify({
        'anio': anio,
        'periodo_id': periodo_id,
        'orden': 'pernr' if orden == 'pernr' else 'horas',
        'empleados': [
            {
                'pernr': row.pernr,
                'nombre': row.nombre,
                'apellidos': row.apellidos,
                'horas_extra': int(row.horas_extra or 0),
            }
            for row in empleados
        ],
        'departamentos': departamentos,
        'total': total,
        'periodos': [
            {
                'id': periodo.ID,
                'ejercicio': periodo.EJERCICIO,
                'descripcion': periodo.DESCRIPTION or f'Periodo {periodo.ID}',
                'fecha_inicio': periodo.FECHAINI.isoformat() if periodo.FECHAINI else None,
                'fecha_fin': periodo.FECHAFIN.isoformat() if periodo.FECHAFIN else None,
            }
            for periodo in periodos
        ],
    }), 200

# ---------------------------------------------------------
# ENDPOINTS EXISTENTES
# ---------------------------------------------------------

@partes_bp.route('', methods=['GET'])
def get_partes():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = ZParte.query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "partes": partes_schema.dump(pagination.items)
    }), 200

@partes_bp.route('/empleado/<string:pernr>', methods=['GET'])
def get_partes_empleado(pernr):
    partes = ZParte.query.filter_by(PERNR=pernr).all()
    if not partes:
        return jsonify({"message": f"No se encontraron partes para el empleado {pernr}"}), 404
    return jsonify(partes_schema.dump(partes)), 200

# ---------------------------------------------------------
# PLANTILLA / EFECTIVOS ACTIVOS
# ---------------------------------------------------------

@partes_bp.route('/plantilla-resumen', methods=['GET'])
def get_plantilla_resumen():
    """
    Devuelve el total de empleados activos (ACTIVE = 1) en userpayroll
    junto con el desglose de activos por grupo, área y departamento.
    """
    grupo = request.args.get('grupo', '').strip()
    direccion = request.args.get('direccion', '').strip()

    filtros = [UserPayroll.ACTIVE == True]  # noqa: E712
    if grupo and grupo.upper() != 'TODOS':
        filtros.append(GruposPayroll.NAME == grupo)
    if direccion and direccion.upper() != 'TODAS':
        filtros.append(AreasPayroll.NAME == direccion)

    total_plantilla = db.session.query(func.count(UserPayroll.ID)) \
        .outerjoin(GruposPayroll, UserPayroll.GRUPO == GruposPayroll.CODE) \
        .outerjoin(AreasPayroll, UserPayroll.AREA == AreasPayroll.CODE) \
        .filter(*filtros).scalar() or 0

    por_grupo = db.session.query(
        func.coalesce(GruposPayroll.NAME, 'Sin grupo').label('nombre'),
        func.count(UserPayroll.ID).label('total'),
    ).select_from(UserPayroll) \
     .outerjoin(GruposPayroll, UserPayroll.GRUPO == GruposPayroll.CODE) \
     .outerjoin(AreasPayroll, UserPayroll.AREA == AreasPayroll.CODE) \
     .filter(*filtros) \
     .group_by(GruposPayroll.NAME) \
     .order_by(func.count(UserPayroll.ID).desc()).all()

    por_area = db.session.query(
        func.coalesce(AreasPayroll.NAME, 'Sin área').label('nombre'),
        func.count(UserPayroll.ID).label('total'),
    ).select_from(UserPayroll) \
     .outerjoin(GruposPayroll, UserPayroll.GRUPO == GruposPayroll.CODE) \
     .outerjoin(AreasPayroll, UserPayroll.AREA == AreasPayroll.CODE) \
     .filter(*filtros) \
     .group_by(AreasPayroll.NAME) \
     .order_by(func.count(UserPayroll.ID).desc()).all()

    por_departamento = db.session.query(
        func.coalesce(DepartmentPayroll.NAME, 'Sin departamento').label('nombre'),
        func.count(UserPayroll.ID).label('total'),
    ).select_from(UserPayroll) \
     .outerjoin(GruposPayroll, UserPayroll.GRUPO == GruposPayroll.CODE) \
     .outerjoin(AreasPayroll, UserPayroll.AREA == AreasPayroll.CODE) \
     .outerjoin(DepartmentPayroll, UserPayroll.DEPARTMENT == DepartmentPayroll.CODE) \
     .filter(*filtros) \
     .group_by(DepartmentPayroll.NAME) \
     .order_by(func.count(UserPayroll.ID).desc()).all()

    return jsonify({
        'total_plantilla': int(total_plantilla),
        'por_grupo': [row._asdict() for row in por_grupo],
        'por_area': [row._asdict() for row in por_area],
        'por_departamento': [row._asdict() for row in por_departamento],
    }), 200


# ---------------------------------------------------------
# LAS 4 PANTALLAS DE LOOKER STUDIO
# ---------------------------------------------------------

# PANTALLA 1: HE por Períodos - Vista Departamento
@partes_bp.route('/resumen-departamento', methods=['GET'])
def get_resumen_departamento():
    anio = request.args.get('anio', '2026', type=str)
    norm, comp, busca, buscanp, combo, total = get_he_expressions()

    query = db.session.query(
        ZParte.DPTO.label('departamento'),
        func.coalesce(func.sum(norm), 0).label('normales'),
        func.coalesce(func.sum(comp), 0).label('compensar'),
        func.coalesce(func.sum(busca), 0).label('busca'),
        func.coalesce(func.sum(buscanp), 0).label('buscanp'),
        func.coalesce(func.sum(combo), 0).label('combo'),
        func.coalesce(func.sum(total), 0).label('total')
    ).filter(ZParte.EJERC == anio).group_by(ZParte.DPTO).all()

    return jsonify([row._asdict() for row in query]), 200


# PANTALLA 2: HE por Períodos - Vista Trabajador
@partes_bp.route('/resumen-trabajador', methods=['GET'])
def get_resumen_trabajador():
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
        func.coalesce(func.sum(norm + busca), 0).label('totalretrib')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio)\
     .group_by(ZParte.PERNR, UserPayroll.NAME).all()

    return jsonify([row._asdict() for row in query]), 200


# PANTALLA 3: HE Comité
@partes_bp.route('/comite', methods=['GET'])
def get_he_comite():
    anio = request.args.get('anio', '2026', type=str)
    _, _, _, _, _, total = get_he_expressions()

    query = db.session.query(
        ZParte.PERNR.label('id_empleado'),
        func.coalesce(func.sum(total), 0).label('horas_extras')
    ).filter(ZParte.EJERC == anio).group_by(ZParte.PERNR).all()

    return jsonify([row._asdict() for row in query]), 200


# PANTALLA 4: Ranking HE Combo y Totales
@partes_bp.route('/ranking-combo', methods=['GET'])
def get_ranking_combo():
    anio = request.args.get('anio', '2026', type=str)
    mes_desde = max(request.args.get('mes_desde', 1, type=int), 1)
    mes_hasta = min(request.args.get('mes_hasta', 12, type=int), 12)
    anio_natural = request.args.get('anio_natural', 'false').lower() in {'true', '1', 'si', 'yes'}
    departamento = request.args.get('departamento', '').strip()
    pernr = request.args.get('pernr', '').strip()
    estado = request.args.get('estado', '').strip()
    periodo_id = request.args.get('periodo_id', '').strip()

    if mes_desde > mes_hasta:
        return jsonify({'message': 'El periodo de meses no es válido.'}), 400

    periodos = ZPeriodos.query.filter_by(EJERCICIO=anio).order_by(ZPeriodos.ID).all()
    periodo_seleccionado = next((periodo for periodo in periodos if periodo.ID == periodo_id), None)
    if periodo_id and not anio_natural and not periodo_seleccionado:
        return jsonify({'message': 'El periodo seleccionado no existe para el ejercicio indicado.'}), 400

    if anio_natural:
        filtros = [ZParte.PADAT.between(
            date(int(anio), mes_desde, 1),
            date(int(anio), mes_hasta, calendar.monthrange(int(anio), mes_hasta)[1]),
        )]
    elif periodo_seleccionado:
        filtros = [ZParte.EJERC == periodo_seleccionado.EJERCICIO, ZParte.MES == periodo_seleccionado.ID]
    else:
        filtros = [ZParte.EJERC == anio, ZParte.MES.in_([f'{mes:02d}' for mes in range(mes_desde, mes_hasta + 1)])]

    if departamento:
        filtros.append(ZParte.DPTO == departamento)
    if pernr:
        filtros.append(ZParte.PERNR == pernr)
    if estado:
        filtros.append(ZParte.STAT == estado)

    def suma(*nombres):
        cols = [getattr(ZParte, nombre) for nombre in nombres]
        res = cols[0]
        for c in cols[1:]:
            res = res + c
        return res

    combo_programadas = suma('DLCOP', 'DFCOP', 'NLCOP', 'NFCOP')
    total_he = suma(
        'DL', 'DF', 'NL', 'NF', 'DLB', 'DFB', 'NLB', 'NFB',
        'DLF', 'DFF', 'NLF', 'NFF', 'DLC', 'DFC', 'NLC', 'NFC',
        'DLCO', 'DFCO', 'NLCO', 'NFCO', 'DLBN', 'DFBN', 'NLBN', 'NFBN',
        'DLCOP', 'DFCOP', 'NLCOP', 'NFCOP',
    )
    comp_dl = ZParte.DL
    comp_df = ZParte.DF
    comp_nl = ZParte.NL
    comp_nf = ZParte.NF
    compensables = comp_dl + comp_df + comp_nl + comp_nf
    compensables_convertidas = (comp_dl * 1.6) + (comp_df * 2.0) + (comp_nl * 2.0) + (comp_nf * 2.5)

    query = db.session.query(
        ZParte.PERNR.label('pernr'), UserPayroll.NAME.label('nombre'), UserPayroll.SURNAME.label('apellidos'),
        func.coalesce(func.sum(combo_programadas), 0).label('combo_programadas'),
        func.coalesce(func.sum(total_he), 0).label('total_he'),
        func.coalesce(func.sum(compensables), 0).label('he_compensables'),
        func.coalesce(func.sum(compensables_convertidas), 0).label('he_compensables_convertidas'),
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER).filter(*filtros) \
     .group_by(ZParte.PERNR, UserPayroll.NAME, UserPayroll.SURNAME) \
     .order_by(func.sum(total_he).desc(), ZParte.PERNR.asc()).all()

    filas = [{
        'pernr': row.pernr, 'nombre': row.nombre, 'apellidos': row.apellidos,
        'combo_programadas': float(row.combo_programadas or 0),
        'total_he': float(row.total_he or 0),
        'he_compensables': float(row.he_compensables or 0),
        'he_compensables_convertidas': round(float(row.he_compensables_convertidas or 0), 2),
    } for row in query]
    departamentos = [row[0] for row in db.session.query(ZParte.DPTO).filter(*filtros).filter(ZParte.DPTO.isnot(None)).distinct().order_by(ZParte.DPTO).all()]

    return jsonify({
        'anio': anio, 'periodo_id': periodo_id, 'filas': filas,
        'departamentos': departamentos,
        'totales': {
            'combo_programadas': sum(f['combo_programadas'] for f in filas),
            'total_he': sum(f['total_he'] for f in filas),
            'he_compensables': sum(f['he_compensables'] for f in filas),
            'he_compensables_convertidas': round(sum(f['he_compensables_convertidas'] for f in filas), 2),
        },
        'periodos': [{
            'id': p.ID, 'ejercicio': p.EJERCICIO, 'descripcion': p.DESCRIPTION or f'Periodo {p.ID}',
            'fecha_inicio': p.FECHAINI.isoformat() if p.FECHAINI else None,
            'fecha_fin': p.FECHAFIN.isoformat() if p.FECHAFIN else None,
        } for p in periodos],
    }), 200
# ---------------------------------------------------------
# PANTALLAS ADICIONALES: SPs, BUSCAS Y TOP 10
# ---------------------------------------------------------

# PANTALLA: Total SP Creadas + Evolutivo (Últimos 12 y 24 meses)
@partes_bp.route('/sp-evolutivo', methods=['GET'])
def get_sp_evolutivo():
    # Agrupación por trabajador para el acumulado de partes (recuento de registros o campo SP)
    sp_12m = db.session.query(
        UserPayroll.NAME.label('trabajador'),
        ZParte.PERNR.label('id'),
        func.count(ZParte.id).label('sp')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .group_by(ZParte.PERNR, UserPayroll.NAME)\
     .order_by(func.count(ZParte.id).desc()).limit(20).all()

    return jsonify({
        "sp_ultimos_12_meses": [row._asdict() for row in sp_12m]
    }), 200


@partes_bp.route('/sp-resumen-periodos', methods=['GET'])
def get_sp_resumen_periodos():
    fecha_hasta_texto = request.args.get('fecha_hasta', '').strip()
    if fecha_hasta_texto:
        try:
            fecha_hasta = date.fromisoformat(fecha_hasta_texto)
        except ValueError:
            return jsonify({'message': 'La fecha_hasta no es válida. Usa el formato YYYY-MM-DD.'}), 400
    else:
        fecha_hasta = date.today()

    def restar_meses(fecha, meses):
        total_meses = fecha.year * 12 + fecha.month - 1 - meses
        anio, mes = divmod(total_meses, 12)
        dia = min(fecha.day, calendar.monthrange(anio, mes + 1)[1])
        return date(anio, mes + 1, dia)

    def resumen_periodo(meses):
        fecha_desde = restar_meses(fecha_hasta, meses)
        filtros = [
            ZParte.PADAT.between(fecha_desde, fecha_hasta),
            func.trim(func.coalesce(ZParte.SP, '')) != '',
            func.trim(func.coalesce(ZParte.SP, '')) != '0',
        ]

        personas = db.session.query(
            UserPayroll.NAME.label('nombre'),
            UserPayroll.SURNAME.label('apellidos'),
            ZParte.PERNR.label('id'),
            ZParte.DPTO.label('departamento'),
            func.count().label('sp'),
        ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER) \
         .filter(*filtros) \
         .group_by(ZParte.PERNR, UserPayroll.NAME, UserPayroll.SURNAME, ZParte.DPTO) \
         .order_by(func.count().desc(), ZParte.PERNR.asc()).all()

        departamentos = db.session.query(
            ZParte.DPTO.label('departamento'),
            func.count().label('sp'),
        ).filter(*filtros) \
         .group_by(ZParte.DPTO) \
         .order_by(func.count().desc(), ZParte.DPTO.asc()).all()

        total_personas = sum(int(row.sp or 0) for row in personas)
        return {
            'meses': meses,
            'fecha_desde': fecha_desde.isoformat(),
            'fecha_hasta': fecha_hasta.isoformat(),
            'personas': [row._asdict() for row in personas],
            'departamentos': [row._asdict() for row in departamentos],
            'total_sp': total_personas,
            'total_personas': len(personas),
        }

    return jsonify({
        'fecha_hasta': fecha_hasta.isoformat(),
        'periodos': {
            '12': resumen_periodo(12),
            '24': resumen_periodo(24),
        },
    }), 200


# PANTALLA: Buscas, Sustituciones, Llamadas y Dietas
@partes_bp.route('/buscas-dietas', methods=['GET'])
def get_buscas_dietas():
    anio = request.args.get('anio', '2026', type=str)
    
    # Vista por departamento sumando BLV, BSDF, PA, SUST, etc.
    por_dpto = db.session.query(
        ZParte.DPTO.label('departamento'),
        func.coalesce(func.sum(ZParte.DLB + ZParte.DFB + ZParte.NLB + ZParte.NFB), 0).label('blv'),
        func.coalesce(func.sum(ZParte.DLBN + ZParte.DFBN + ZParte.NLBN + ZParte.NFBN), 0).label('bsdf'),
        func.coalesce(func.sum(ZParte.PA), 0).label('pa'),
        func.coalesce(func.sum(ZParte.SUST), 0).label('sust'),
        func.coalesce(func.sum(ZParte.LLAMADA), 0).label('llamada'),
        func.coalesce(func.sum(ZParte.DIETA), 0).label('d')
    ).filter(ZParte.EJERC == anio).group_by(ZParte.DPTO).all()

    return jsonify({
        "por_departamento": [row._asdict() for row in por_dpto]
    }), 200


# PANTALLA: Top 10 Multimétrica (HE, Busca, PA, Art. 21, etc.)
@partes_bp.route('/top10', methods=['GET'])
def get_top10():
    anio = request.args.get('anio', '2026', type=str)
    _, _, busca, _, _, total_he = get_he_expressions()

    top_busca = db.session.query(
        UserPayroll.NAME.label('trabajador'),
        ZParte.PERNR.label('id'),
        func.coalesce(func.sum(busca), 0).label('valor')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio)\
     .group_by(ZParte.PERNR, UserPayroll.NAME)\
     .order_by(func.sum(busca).desc()).limit(10).all()

    top_pa = db.session.query(
        UserPayroll.NAME.label('trabajador'),
        ZParte.PERNR.label('id'),
        func.coalesce(func.sum(ZParte.PA), 0).label('valor')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio)\
     .group_by(ZParte.PERNR, UserPayroll.NAME)\
     .order_by(func.sum(ZParte.PA).desc()).limit(10).all()

    return jsonify({
        "top_10_busca": [row._asdict() for row in top_busca],
        "top_10_pa": [row._asdict() for row in top_pa]
    }), 200

# ---------------------------------------------------------
# PANTALLA: KM y Teletrabajo
# ---------------------------------------------------------

@partes_bp.route('/km-teletra-bajo', methods=['GET'])
def get_km_teletrabajo():
    anio = request.args.get('anio', '2026', type=str)

    # Top 10 KM por trabajador
    top_km = db.session.query(
        UserPayroll.NAME.label('trabajador'),
        ZParte.PERNR.label('id'),
        func.coalesce(func.sum(ZParte.KM), 0).label('total_km')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio)\
     .group_by(ZParte.PERNR, UserPayroll.NAME)\
     .order_by(func.sum(ZParte.KM).desc()).limit(10).all()

    # Días de Teletrabajo por Trabajador (asumiendo campo TELETRABAJO o similar)
    # Ajusta ZParte.TELETRABAJO al nombre exacto de tu columna si difiere
    detalle_teletrabajo = db.session.query(
        UserPayroll.NAME.label('trabajador'),
        ZParte.DPTO.label('departamento'),
        func.coalesce(func.sum(ZParte.TELETRABAJO), 0).label('dias_teletrabajo')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio)\
     .group_by(ZParte.PERNR, UserPayroll.NAME, ZParte.DPTO)\
     .order_by(func.sum(ZParte.TELETRABAJO).desc()).all()

    return jsonify({
        "top_10_km": [row._asdict() for row in top_km],
        "detalle_teletrabajo": [row._asdict() for row in detalle_teletrabajo]
    }), 200
# ---------------------------------------------------------
# PANTALLAS FINALES: Control Art. 21, Direcciones, Observaciones y Estados
# ---------------------------------------------------------

# PANTALLA: Control Art. 21 Desc
@partes_bp.route('/control-art21', methods=['GET'])
def get_control_art21():
    anio = request.args.get('anio', '2026', type=str)
    
    query = db.session.query(
        UserPayroll.NAME.label('nombre'),
        ZParte.PERNR.label('id'),
        ZParte.PADAT.label('fecha'),
        ZParte.DPTO.label('grupo'),
        ZParte.OBSERV1.label('observ_1'),
        ZParte.OBSERV2.label('observ_2'),
        ZParte.ART21.label('art_21_desc')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio, ZParte.ART21 > 0).all()

    return jsonify([row._asdict() for row in query]), 200


# PANTALLA: Vista Direcciones - Personas
@partes_bp.route('/direcciones-personas', methods=['GET'])
def get_direcciones_personas():
    query = db.session.query(
        UserPayroll.NAME.label('nombre'),
        UserPayroll.NUMPER.label('id'),
        UserPayroll.DIRECCION.label('direccion'),
        UserPayroll.AREA.label('area'),
        UserPayroll.GRUPO_EPARTES.label('grupo_epartes')
    ).all()

    return jsonify([row._asdict() for row in query]), 200


# PANTALLA: Vista Observaciones (SPs)
@partes_bp.route('/observaciones', methods=['GET'])
def get_observaciones():
    anio = request.args.get('anio', '2026', type=str)
    
    query = db.session.query(
        UserPayroll.NAME.label('nombre_trabajador'),
        ZParte.PERNR.label('numero_empleado'),
        ZParte.PADAT.label('fecha_parte'),
        ZParte.SP.label('sp'),
        ZParte.OBSERV1.label('observaciones_1'),
        ZParte.OBSERV2.label('observaciones_2')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio).all()

    return jsonify([row._asdict() for row in query]), 200


# PANTALLA: Comprobación Estados
@partes_bp.route('/comprobacion-estados', methods=['GET'])
def get_comprobacion_estados():
    anio = request.args.get('anio', '2026', type=str)
    
    query = db.session.query(
        UserPayroll.NAME.label('nombre_trabajador'),
        ZParte.PERNR.label('numero_empleado'),
        ZParte.PADAT.label('fecha_parte'),
        ZParte.ESTADO.label('estado')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio).all()

    return jsonify([row._asdict() for row in query]), 200
# ---------------------------------------------------------
# BLOQUE FINAL: Las 9 vistas pendientes del menú lateral
# ---------------------------------------------------------

# 1. Índice de reportes (KPIs y Resumen general de bienvenida)
@partes_bp.route('/indice-reportes', methods=['GET'])
def get_indice_reportes():
    anio = request.args.get('anio', '2026', type=str)
    total_partes = db.session.query(func.count(ZParte.id)).filter(ZParte.EJERC == anio).scalar()
    total_trabajadores = db.session.query(func.count(db.distinct(ZParte.PERNR))).filter(ZParte.EJERC == anio).scalar()
    
    return jsonify({
        "anio": anio,
        "total_partes": total_partes or 0,
        "total_trabajadores_activos": total_trabajadores or 0
    }), 200


# 2. HE año natural (Acumulado de horas extras por año natural)
@partes_bp.route('/he-anio-natural', methods=['GET'])
def get_he_anio_natural():
    anio = request.args.get('anio', '2026', type=str)
    _, _, _, _, _, total_he = get_he_expressions()
    
    query = db.session.query(
        UserPayroll.NAME.label('trabajador'),
        ZParte.PERNR.label('id'),
        func.coalesce(func.sum(total_he), 0).label('total_he_anio')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio)\
     .group_by(ZParte.PERNR, UserPayroll.NAME)\
     .order_by(func.sum(total_he).desc()).all()

    return jsonify([row._asdict() for row in query]), 200


# 3. Total SP retribuidas
@partes_bp.route('/sp-retribuidas', methods=['GET'])
def get_sp_retribuidas():
    anio = request.args.get('anio', '2026', type=str)
    
    query = db.session.query(
        UserPayroll.NAME.label('trabajador'),
        ZParte.PERNR.label('id'),
        func.count(ZParte.id).label('total_sp_retribuidas')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio, ZParte.SP > 0)\
     .group_by(ZParte.PERNR, UserPayroll.NAME).all()

    return jsonify([row._asdict() for row in query]), 200


# 4. Total SP por mes (Vista agrupada y gráfica mensual)
@partes_bp.route('/sp-por-mes', methods=['GET'])
def get_sp_por_mes():
    anio = request.args.get('anio', '2026', type=str)
    
    query = db.session.query(
        extract('month', ZParte.PADAT).label('mes'),
        func.count(ZParte.id).label('total_sp')
    ).filter(ZParte.EJERC == anio)\
     .group_by(extract('month', ZParte.PADAT))\
     .order_by(extract('month', ZParte.PADAT)).all()

    return jsonify([row._asdict() for row in query]), 200


# 5. Detalle SP RRHH
@partes_bp.route('/sp-detalle-rrhh', methods=['GET'])
def get_sp_detalle_rrhh():
    anio = request.args.get('anio', '2026', type=str)
    
    query = db.session.query(
        UserPayroll.NAME.label('trabajador'),
        ZParte.PERNR.label('id'),
        ZParte.PADAT.label('fecha'),
        ZParte.DPTO.label('departamento'),
        ZParte.SP.label('sp')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio, ZParte.SP > 0).all()

    return jsonify([row._asdict() for row in query]), 200


# 6. PA - NI020
@partes_bp.route('/pa-ni020', methods=['GET'])
def get_pa_ni020():
    anio = request.args.get('anio', '2026', type=str)
    
    query = db.session.query(
        UserPayroll.NAME.label('trabajador'),
        ZParte.PERNR.label('id'),
        ZParte.PADAT.label('fecha'),
        ZParte.PA.label('pa')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio, ZParte.PA > 0).all()

    return jsonify([row._asdict() for row in query]), 200


# 7. Desglose Diario HE (Matriz detallada por día)
@partes_bp.route('/desglose-diario-he', methods=['GET'])
def get_desglose_diario_he():
    anio = request.args.get('anio', '2026', type=str)
    
    query = db.session.query(
        UserPayroll.NAME.label('trabajador'),
        ZParte.PERNR.label('id'),
        ZParte.PADAT.label('fecha'),
        ZParte.DIA.label('dia_semana'),
        ZParte.HPRES.label('horas_presencia')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio).limit(500).all()

    return jsonify([row._asdict() for row in query]), 200


# 8. Detalle evolución años (Comparativa histórica plurianual)
@partes_bp.route('/evolucion-anios', methods=['GET'])
def get_evolucion_anios():
    query = db.session.query(
        ZParte.EJERC.label('anio'),
        func.count(ZParte.id).label('total_partes')
    ).group_by(ZParte.EJERC)\
     .order_by(ZParte.EJERC.asc()).all()

    return jsonify([row._asdict() for row in query]), 200


# 9. Control PA, Llamadas y día (Vista de la imagen 15)
@partes_bp.route('/control-pa-llamadas-dia', methods=['GET'])
def get_control_pa_llamadas_dia():
    anio = request.args.get('anio', '2026', type=str)
    
    query = db.session.query(
        UserPayroll.NAME.label('trabajador'),
        ZParte.PERNR.label('id'),
        ZParte.PADAT.label('fecha'),
        ZParte.DIA.label('dia'),
        ZParte.PA.label('pa'),
        ZParte.LLAMADA.label('llamada')
    ).outerjoin(UserPayroll, ZParte.PERNR == UserPayroll.NUMPER)\
     .filter(ZParte.EJERC == anio, (ZParte.PA > 0) | (ZParte.LLAMADA > 0)).all()

    return jsonify([row._asdict() for row in query]), 200
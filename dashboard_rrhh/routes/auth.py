from extensions import db
from flask import Blueprint, jsonify, request
from models import UserPayroll

# Creamos el blueprint con el prefijo /api para que coincida con Angular
auth_bp = Blueprint('auth', __name__, url_prefix='/api')
ADMIN_EMAIL = 'admin@admin.org'


@auth_bp.route('/get-roles', methods=['POST'])
def get_roles():
  data = request.get_json() or {}
  email = str(data.get('email') or '').strip().lower()

  if not email:
    return jsonify({'message': 'El correo es obligatorio'}), 400

  if email == ADMIN_EMAIL:
    return jsonify({'success': True, 'roles': ['empleado']}), 200

  usuario = db.session.scalar(
      db.select(UserPayroll).where(db.func.lower(UserPayroll.EMAIL) == email)
  )
  if not usuario or not usuario.ACTIVE:
    return jsonify({'message': 'Correo no encontrado en la base de datos.'}), 404

  return jsonify({'success': True, 'roles': ['empleado']}), 200


@auth_bp.route('/login', methods=['POST'])
def login():
  data = request.get_json() or {}
  email = str(data.get('email') or '').strip().lower()
  password = data.get('password') or ''
  rol_seleccionado = data.get('rol', 'empleado')

  if not email:
    return jsonify({'message': 'El correo es obligatorio'}), 400

  if email != ADMIN_EMAIL:
    usuario = db.session.scalar(
        db.select(UserPayroll).where(db.func.lower(UserPayroll.EMAIL) == email)
    )
    if not usuario or not usuario.ACTIVE or not password or password != usuario.PASSWORD:
      return jsonify({'message': 'Correo o contraseña incorrectos.'}), 401

  return jsonify({
      'success': True,
      'user': {
          'email': email,
          'rolActivo': rol_seleccionado,
      },
  }), 200
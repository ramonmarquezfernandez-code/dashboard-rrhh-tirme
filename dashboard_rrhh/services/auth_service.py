import bcrypt
from flask_jwt_extended import create_access_token

from extensions import db
from models import UserPayroll
from services.rol_service import ROL_MANDO, RolService

# Hash de una contraseña cualquiera. Se compara contra él cuando el correo no
# existe, para que el tiempo de respuesta no delate qué correos están registrados.
_HASH_FICTICIO = bcrypt.hashpw(b'password-ficticia', bcrypt.gensalt())


class AuthService:
    """Autenticación de usuarios de userpayroll con contraseñas bcrypt."""

    @staticmethod
    def hashear_password(password):
        """Devuelve el hash bcrypt (60 caracteres) de una contraseña en claro."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def buscar_usuario_activo(email):
        email = str(email or '').strip().lower()
        if not email:
            return None
        usuario = db.session.scalar(
            db.select(UserPayroll).where(db.func.lower(UserPayroll.EMAIL) == email)
        )
        if not usuario or not usuario.ACTIVE:
            return None
        return usuario

    @staticmethod
    def verificar_password(usuario, password):
        """True si la contraseña coincide con el hash bcrypt de userpayroll.PASSWORD."""
        password_bytes = str(password or '').encode('utf-8')
        if usuario is None or not usuario.PASSWORD:
            bcrypt.checkpw(password_bytes, _HASH_FICTICIO)
            return False
        try:
            return bcrypt.checkpw(password_bytes, usuario.PASSWORD.encode('utf-8'))
        except ValueError:
            # El valor guardado no es un hash bcrypt válido (p. ej. texto plano)
            return False

    @staticmethod
    def emitir_token(usuario, rol, rol_service=None):
        """Crea el JWT con los datos que necesita el filtro de acceso."""
        rol_service = rol_service or RolService(usuario.NUMPER)
        codgrs = sorted(rol_service.codgrs_mando()) if rol == ROL_MANDO else []
        return create_access_token(
            identity=usuario.NUMPER,
            additional_claims={
                'email': (usuario.EMAIL or '').lower(),
                'rol_activo': rol,
                'codgrs': codgrs,
            },
        )

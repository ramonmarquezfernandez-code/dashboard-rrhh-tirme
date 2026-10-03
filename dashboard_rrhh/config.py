import os
from datetime import timedelta

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', None) or None  # Si está vacío lo pasa a None
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'epartes_local')

    # URL.create maneja de forma transparente si hay o no contraseña
    SQLALCHEMY_DATABASE_URI = URL.create(
        drivername="mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        query={"charset": "utf8mb4"}
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT (flask-jwt-extended). Si no se define una clave propia, se usa SECRET_KEY.
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    # Necesario para que Flask-RESTX no convierta los errores de JWT en un 500
    PROPAGATE_EXCEPTIONS = True
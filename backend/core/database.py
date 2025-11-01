from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys
from dotenv import load_dotenv

load_dotenv()

"""
Configuración de base de datos portable:
 - En modo empaquetado (PyInstaller), guarda la BD en `<dir_del_exe>/data/sistema_notas.db`.
 - En modo desarrollo (python normal), usa `<repo>/backend/data/sistema_notas.db`.
Esto asegura que copiar la carpeta del ejecutable sea suficiente para llevar los datos.
"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(BASE_DIR)

# Detectar si estamos corriendo como ejecutable empaquetado
if getattr(sys, "frozen", False):
    app_dir = os.path.dirname(sys.executable)
else:
    # Directorio base del proyecto (padre de backend)
    project_root = os.path.dirname(BACKEND_DIR)
    app_dir = os.path.join(project_root, "backend")

# Carpeta de datos persistentes junto al ejecutable o backend
DATA_DIR = os.path.join(app_dir, "data")
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    # Si no se puede crear, usar directorio actual como respaldo
    DATA_DIR = os.path.join(os.getcwd(), "data")
    os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "sistema_notas.db")
print(f"Ruta de la base de datos: {DB_PATH}")

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
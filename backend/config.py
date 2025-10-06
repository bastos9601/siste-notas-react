import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de la aplicación
SECRET_KEY = os.getenv("SECRET_KEY", "tu-clave-secreta-muy-segura-aqui-cambiar-en-produccion")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sistema_notas.db")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Usuario
from auth import get_password_hash

# Configuración de la base de datos (SQLite local en backend)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sistema_notas.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def actualizar_admin(email_nuevo: str, password_nueva: str, email_actual: str = "admin@sistema.com"):
    db = SessionLocal()
    try:
        # Intentar localizar el admin por email actual; si no existe, tomar el primero por rol
        admin = db.query(Usuario).filter(Usuario.email == email_actual).first()
        if not admin:
            admin = db.query(Usuario).filter(Usuario.rol == "admin").order_by(Usuario.id.asc()).first()
        if not admin:
            print("❌ No se encontró ningún usuario con rol admin")
            return False

        # Verificar que el nuevo email no esté usado por otro usuario
        existing = db.query(Usuario).filter(Usuario.email == email_nuevo, Usuario.id != admin.id).first()
        if existing:
            print(f"❌ El email {email_nuevo} ya está registrado por otro usuario (ID {existing.id})")
            return False

        # Aplicar cambios
        admin.email = email_nuevo
        admin.password_hash = get_password_hash(password_nueva)
        # Opcional: actualizar nombre usando la parte antes del @
        if not admin.nombre or admin.nombre.strip() == "" or admin.nombre.lower() == "administrador":
            admin.nombre = email_nuevo.split('@')[0]

        db.commit()
        db.refresh(admin)
        print("✅ Admin actualizado exitosamente")
        print(f"   ID: {admin.id}")
        print(f"   Email nuevo: {admin.email}")
        print(f"   Rol: {admin.rol}")
        return True
    except Exception as e:
        print(f"❌ Error actualizando admin: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Valores solicitados
    actualizar_admin(email_nuevo="adelinacampos999@gmail.com", password_nueva="123456")
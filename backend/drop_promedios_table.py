from sqlalchemy import inspect
from database import engine
from models import Promedio


def drop_promedios_table():
    """Eliminar la tabla 'promedios' si existe."""
    insp = inspect(engine)
    if insp.has_table("promedios"):
        try:
            Promedio.__table__.drop(bind=engine)
            print("Tabla 'promedios' eliminada correctamente.")
        except Exception as e:
            print(f"Error al eliminar la tabla 'promedios': {e}")
    else:
        print("La tabla 'promedios' no existe o ya fue eliminada.")


if __name__ == "__main__":
    drop_promedios_table()
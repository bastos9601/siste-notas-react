from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, admin, docente, alumno
from database import engine, Base, get_db
from models import Usuario
from sqlalchemy.orm import Session

# Crear las tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gestión de Notas",
    description="API para gestión académica de notas con roles de Admin, Docente y Alumno",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server (puerto original)
        "http://localhost:3001",  # React dev server (nuevo puerto)
        "http://127.0.0.1:3000",  # Alternativa localhost
        "http://127.0.0.1:3001",  # Alternativa localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/auth", tags=["autenticación"])
app.include_router(admin.router, prefix="/admin", tags=["administrador"])
app.include_router(docente.router, prefix="/docente", tags=["docente"])
app.include_router(alumno.router, prefix="/alumno", tags=["alumno"])

@app.get("/")
async def root():
    return {"message": "Sistema de Gestión de Notas API"}


@app.get("/debug/users")
async def debug_users(db: Session = Depends(get_db)):
    """Endpoint de debug para verificar usuarios"""
    import os
    from sqlalchemy import text
    
    # Información de debug adicional
    debug_info = {
        "database_url": os.getenv("DATABASE_URL", "sqlite:///../sistema_notas.db"),
        "current_directory": os.getcwd(),
        "database_exists": os.path.exists("../sistema_notas.db"),
        "database_path": os.path.abspath("../sistema_notas.db") if os.path.exists("../sistema_notas.db") else None
    }
    
    # Consulta usando SQLAlchemy ORM
    users = db.query(Usuario).all()
    
    # Consulta directa usando SQL
    direct_count = 0
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM usuarios"))
            direct_count = result.fetchone()[0]
    except Exception as e:
        debug_info["sql_error"] = str(e)
    
    return {
        "total_users_orm": len(users),
        "total_users_sql": direct_count,
        "debug_info": debug_info,
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "nombre": user.nombre,
                "rol": user.rol,
                "activo": user.activo
            }
            for user in users
        ]
    }

@app.get("/debug/database")
async def debug_database():
    """Endpoint de debug para verificar configuración de base de datos"""
    import os
    from database import DATABASE_URL
    return {
        "database_url": DATABASE_URL,
        "current_directory": os.getcwd(),
        "database_exists": os.path.exists("sistema_notas.db"),
        "database_path": os.path.abspath("sistema_notas.db") if os.path.exists("sistema_notas.db") else None
    }

@app.get("/debug/users-detailed")
async def debug_users_detailed(db: Session = Depends(get_db)):
    """Endpoint de debug detallado para verificar usuarios"""
    import os
    users = db.query(Usuario).all()
    return {
        "total_users": len(users),
        "database_url": os.getenv("DATABASE_URL", "sqlite:///../sistema_notas.db"),
        "current_directory": os.getcwd(),
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "nombre": user.nombre,
                "rol": user.rol,
                "activo": user.activo,
                "password_hash": user.password_hash[:50] + "..." if user.password_hash else None
            }
            for user in users
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import auth, admin, docente, alumno, historial
# Añadir import del nuevo router de chatbot
from routers import chatbot
from core.auth import require_role, get_password_hash  # para dependencias de rol y hash de contraseñas
from core.database import engine, Base, get_db, SessionLocal
from models import Usuario
from sqlalchemy.orm import Session
import os
import sys
from starlette.responses import FileResponse

"""
Establecer directorios y CWD de forma portable:
 - En ejecutable: usar el directorio del .exe como CWD.
 - En desarrollo: usar el directorio `backend/` como CWD.
"""
backend_dir = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = backend_dir
try:
    os.chdir(app_dir)
except Exception:
    pass
print(f"Directorio de trabajo actual: {os.getcwd()}")

# Crear las tablas
Base.metadata.create_all(bind=engine)

# Crear usuario admin por defecto si no existe
try:
    db = SessionLocal()
    try:
        default_email = "admin@gmail.com"
        existing_admin = db.query(Usuario).filter(Usuario.email == default_email).first()
        if not existing_admin:
            admin_user = Usuario(
                nombre="Admin",
                email=default_email,
                password_hash=get_password_hash("admin123"),
                rol="admin",
                activo=True
            )
            db.add(admin_user)
            db.commit()
            print("Creado usuario admin por defecto: admin@gmail.com / admin123")
        else:
            print("Usuario admin por defecto ya existe: admin@gmail.com")
    finally:
        db.close()
except Exception as e:
    print(f"Error creando admin por defecto: {e}")

# Asegurar columna modo_oscuro en configuracion_sistema (SQLite)
try:
    from sqlalchemy import text
    with engine.connect() as conn:
        info = conn.execute(text("PRAGMA table_info(configuracion_sistema)")).fetchall()
        cols = [row[1] for row in info]  # nombre de columnas
        if 'modo_oscuro' not in cols:
            conn.execute(text("ALTER TABLE configuracion_sistema ADD COLUMN modo_oscuro INTEGER DEFAULT 0"))
except Exception as _e:
    # Silencioso en producción, solo asegurar que la app arranque
    pass

app = FastAPI(
    title="Sistema de Gestión de Notas",
    description="API para gestión académica de notas con roles de Admin, Docente y Alumno",
    version="1.0.0"
)

# Configurar CORS
# En la configuración CORS (líneas 20-25):
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las origenes para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Servir archivos estáticos para logos subidos localmente
uploads_root = os.path.join(app_dir, "uploads")
os.makedirs(os.path.join(uploads_root, "logos"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_root), name="uploads")

"""
Servir frontend React (build) de forma portable.
 - En ejecutable: buscar dentro de `_MEIPASS/frontend/build` si fue empaquetado con --add-data.
 - En desarrollo: usar `../frontend/build` relativo al repo.
 - Proveer ruta raíz y catch-all para SPA.
"""
def get_frontend_build_dir():
    # PyInstaller: archivos empaquetados se extraen en sys._MEIPASS
    if hasattr(sys, "_MEIPASS"):
        candidate = os.path.join(sys._MEIPASS, "frontend", "build")
        if os.path.exists(candidate):
            return candidate
    # Desarrollo: relativo al proyecto
    project_root = os.path.dirname(backend_dir)
    candidate = os.path.join(project_root, "frontend", "build")
    return candidate

# Incluir routers PRIMERO (antes del catch-all del frontend)
app.include_router(auth.router, prefix="/auth", tags=["autenticación"])
app.include_router(admin.router, prefix="/admin", tags=["administrador"])
app.include_router(docente.router, prefix="/docente", tags=["docente"])
app.include_router(alumno.router, prefix="/alumno", tags=["alumno"])
app.include_router(historial.router, prefix="/historial", tags=["historial académico"])
# Incluir el router de chatbot
app.include_router(chatbot.router, prefix="", tags=["chatbot"])
# Incluir router de configuración
from routers import configuracion
app.include_router(configuracion.router, prefix="", tags=["configuración"])

# Configurar frontend DESPUÉS de los routers de API
build_dir = get_frontend_build_dir()
if os.path.exists(build_dir):
    # Servir assets estáticos desde build/static
    static_dir = os.path.join(build_dir, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Servir plantillas desde build/templates si existen
    templates_dir = os.path.join(build_dir, "templates")
    if os.path.exists(templates_dir):
        app.mount("/templates", StaticFiles(directory=templates_dir), name="templates")

    index_html = os.path.join(build_dir, "index.html")
    @app.get("/")
    async def serve_index():
        return FileResponse(index_html)

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Catch-all para rutas del frontend (solo rutas que no sean de API)
        if os.path.exists(index_html):
            return FileResponse(index_html)
        return {"detail": "Frontend no construido"}
else:
    print(f"Frontend build no encontrado en: {build_dir}. Sólo API disponible.")
    
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
        "database_url": os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sistema_notas.db')}"),
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
    from core.database import DATABASE_URL
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
        "database_url": os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sistema_notas.db')}"),
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


@app.get("/debug/routes")
async def debug_routes():
    """Devuelve la lista de rutas registradas y sus métodos (útil para depuración)."""
    routes = []
    for route in app.router.routes:
        try:
            methods = list(route.methods) if hasattr(route, 'methods') and route.methods else []
            path = getattr(route, 'path', None) or getattr(route, 'rule', None)
            routes.append({
                'path': path,
                'name': getattr(route, 'name', None),
                'methods': methods
            })
        except Exception:
            continue
    return {"count": len(routes), "routes": routes}

# Ruta directa para enviar reporte por correo, como respaldo si el router no se actualiza
@app.post("/docente/reportes/enviar-email")
async def enviar_reporte_email_direct(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Proxy que delega al handler del router de docente para enviar el reporte por email.
    Esto garantiza que la ruta exista aun cuando el servidor no recargó correctamente el módulo docente.
    """
    from routers.docente import enviar_reporte_email as enviar
    return await enviar(payload, db, current_user)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

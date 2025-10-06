from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, admin, docente, alumno
from database import engine, Base

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

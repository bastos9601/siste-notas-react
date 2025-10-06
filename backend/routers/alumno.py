from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Usuario, Alumno, Asignatura, Nota, matriculas
from schemas import (
    Asignatura as AsignaturaSchema,
    Nota as NotaSchema,
    Alumno as AlumnoSchema
)
from auth import require_role, get_password_hash, verify_password
from pydantic import BaseModel

router = APIRouter()

# Esquema para cambiar contraseña
class CambiarContrasenaRequest(BaseModel):
    contrasena_actual: str
    nueva_contrasena: str

@router.get("/mis-asignaturas", response_model=List[AsignaturaSchema])
async def mis_asignaturas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("alumno"))
):
    """Obtener asignaturas matriculadas del alumno actual"""
    # Buscar el alumno asociado al usuario
    alumno = db.query(Alumno).filter(Alumno.usuario_id == current_user.id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    # Obtener asignaturas matriculadas
    matriculas_data = db.execute(
        matriculas.select().where(matriculas.c.alumno_id == alumno.id)
    ).fetchall()
    
    asignaturas = []
    for matricula in matriculas_data:
        asignatura = db.query(Asignatura).filter(Asignatura.id == matricula.asignatura_id).first()
        if asignatura:
            asignaturas.append(asignatura)
    
    return asignaturas

@router.get("/mis-notas", response_model=List[NotaSchema])
async def mis_notas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("alumno"))
):
    """Obtener todas las notas del alumno actual"""
    # Buscar el alumno asociado al usuario
    alumno = db.query(Alumno).filter(Alumno.usuario_id == current_user.id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    notas = db.query(Nota).filter(Nota.alumno_id == alumno.id, Nota.publicada == True).all()
    return notas

@router.get("/asignaturas/{asignatura_id}/notas", response_model=List[NotaSchema])
async def notas_por_asignatura(
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("alumno"))
):
    """Obtener notas del alumno en una asignatura específica"""
    # Buscar el alumno asociado al usuario
    alumno = db.query(Alumno).filter(Alumno.usuario_id == current_user.id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    # Verificar que el alumno está matriculado en la asignatura
    matricula = db.execute(
        matriculas.select().where(
            matriculas.c.alumno_id == alumno.id,
            matriculas.c.asignatura_id == asignatura_id
        )
    ).first()
    
    if not matricula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No estás matriculado en esta asignatura"
        )
    
    notas = db.query(Nota).filter(
        Nota.alumno_id == alumno.id,
        Nota.asignatura_id == asignatura_id,
        Nota.publicada == True
    ).all()
    
    return notas

@router.get("/promedio")
async def mi_promedio(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("alumno"))
):
    """Calcular promedio general del alumno"""
    # Buscar el alumno asociado al usuario
    alumno = db.query(Alumno).filter(Alumno.usuario_id == current_user.id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    notas = db.query(Nota).filter(Nota.alumno_id == alumno.id, Nota.publicada == True).all()
    
    if not notas:
        return {
            "promedio": 0.0,
            "total_notas": 0,
            "mensaje": "No tienes notas registradas"
        }
    
    suma_notas = sum(nota.calificacion for nota in notas)
    promedio = suma_notas / len(notas)
    
    return {
        "promedio": round(promedio, 2),
        "total_notas": len(notas),
        "nota_maxima": max(nota.calificacion for nota in notas),
        "nota_minima": min(nota.calificacion for nota in notas)
    }

@router.get("/promedio-por-asignatura")
async def promedio_por_asignatura(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("alumno"))
):
    """Calcular promedio por asignatura del alumno"""
    # Buscar el alumno asociado al usuario
    alumno = db.query(Alumno).filter(Alumno.usuario_id == current_user.id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    # Obtener asignaturas matriculadas
    matriculas_data = db.execute(
        matriculas.select().where(matriculas.c.alumno_id == alumno.id)
    ).fetchall()
    
    resultados = []
    
    for matricula in matriculas_data:
        asignatura = db.query(Asignatura).filter(Asignatura.id == matricula.asignatura_id).first()
        if asignatura:
            notas = db.query(Nota).filter(
                Nota.alumno_id == alumno.id,
                Nota.asignatura_id == asignatura.id,
                Nota.publicada == True
            ).all()
            
            if notas:
                suma_notas = sum(nota.calificacion for nota in notas)
                promedio = suma_notas / len(notas)
                
                resultados.append({
                    "asignatura_id": asignatura.id,
                    "asignatura_nombre": asignatura.nombre,
                    "promedio": round(promedio, 2),
                    "total_notas": len(notas),
                    "nota_maxima": max(nota.calificacion for nota in notas),
                    "nota_minima": min(nota.calificacion for nota in notas)
                })
            else:
                resultados.append({
                    "asignatura_id": asignatura.id,
                    "asignatura_nombre": asignatura.nombre,
                    "promedio": 0.0,
                    "total_notas": 0,
                    "nota_maxima": 0,
                    "nota_minima": 0
                })
    
    return resultados

@router.get("/perfil", response_model=AlumnoSchema)
async def mi_perfil(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("alumno"))
):
    """Obtener perfil del alumno actual"""
    alumno = db.query(Alumno).filter(Alumno.usuario_id == current_user.id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    return alumno

@router.put("/cambiar-contrasena")
async def cambiar_contrasena(
    contrasena_data: CambiarContrasenaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("alumno"))
):
    """Cambiar contraseña del alumno actual"""
    # Verificar que la contraseña actual sea correcta
    if not verify_password(contrasena_data.contrasena_actual, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta"
        )
    
    # Validar que la nueva contraseña tenga al menos 6 caracteres
    if len(contrasena_data.nueva_contrasena) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 6 caracteres"
        )
    
    # Actualizar la contraseña
    current_user.password_hash = get_password_hash(contrasena_data.nueva_contrasena)
    db.commit()
    
    return {
        "message": "Contraseña actualizada correctamente",
        "alumno": {
            "id": current_user.id,
            "nombre": current_user.nombre,
            "email": current_user.email
        }
    }

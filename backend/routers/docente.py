from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
from core.database import get_db
from models import Usuario, Docente, Asignatura, Alumno, Nota, matriculas
from schemas import (
    Asignatura as AsignaturaSchema,
    Alumno as AlumnoSchema,
    NotaCreate, NotaUpdate, Nota as NotaSchema
)
from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from core.auth import require_role, verify_password, get_password_hash
from datetime import datetime
import os
import csv
import io
from models import ReporteDocente, ReporteArchivoDocente
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from services.promedios import calcular_promedios_alumno, calcular_promedios_asignatura
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from utils.pdf import build_header, apply_table_style, get_styles, build_separator
from services.email_service import send_grades_published_notification
from services.email_service import send_report_with_attachment_bytes

router = APIRouter()

# Utilidad para normalizar y mapear tipos de evaluación provenientes del frontend
def _normalize_tipo_evaluacion(tipo: str) -> str:
    """Normaliza el tipo de evaluación recibido (ids o nombres) a claves internas.
    Retorna uno de: actividades, practicas, parciales, examen_final, promedio_final
    """
    if not tipo:
        return ""
    t = tipo.strip().lower()
    mapping = {
        # Actividades
        "actividad": "actividades",
        "actividades": "actividades",
        # Práctica(s)
        "practica": "practicas",
        "práctica": "practicas",
        "practicas": "practicas",
        "prácticas": "practicas",
        # Parcial(es)
        "parcial": "parciales",
        "parciales": "parciales",
        # Examen Final
        "examen final": "examen_final",
        "final": "examen_final",
        "examen_final": "examen_final",
        # Promedio Final
        "promedio": "promedio_final",
        "promedio final": "promedio_final",
        "promedio_final": "promedio_final",
    }
    return mapping.get(t, t)

# PromedioCreate ya no es necesario - los promedios se calculan dinámicamente
    
class TipoEvaluacion(BaseModel):
    id: str
    nombre: str
    
@router.get("/tipos-evaluacion", response_model=List[TipoEvaluacion])
async def obtener_tipos_evaluacion(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Obtener los tipos de evaluación disponibles en la tabla de promedios"""
    try:
        # Definimos los tipos de evaluación basados en las columnas de la tabla promedios
        tipos_evaluacion = [
            {"id": "actividades", "nombre": "Actividades"},
            {"id": "practicas", "nombre": "Práctica"},
            {"id": "parciales", "nombre": "Parcial"},
            {"id": "examen_final", "nombre": "Examen Final"},
            {"id": "promedio_final", "nombre": "Promedio Final"}
        ]
        return tipos_evaluacion
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener tipos de evaluación: {str(e)}"
        )

@router.post("/guardar-promedios")
async def guardar_promedios(
    promedios: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Los promedios ahora se calculan dinámicamente desde las notas - este endpoint ya no es necesario"""
    return {"message": "Los promedios se calculan automáticamente desde las notas. No es necesario guardarlos manualmente."}

@router.delete("/eliminar-promedios/{alumno_id}/{asignatura_id}")
async def eliminar_promedios(
    alumno_id: int,
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Los promedios ahora se calculan dinámicamente desde las notas - este endpoint ya no es necesario"""
    return {"message": "Los promedios se calculan automáticamente desde las notas. No es necesario eliminarlos manualmente."}

@router.get("/mis-asignaturas", response_model=List[AsignaturaSchema])
async def mis_asignaturas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Obtener asignaturas del docente actual"""
    # Buscar el docente asociado al usuario
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    asignaturas = db.query(Asignatura).filter(Asignatura.docente_id == docente.id).all()
    return asignaturas

@router.get("/asignaturas/{asignatura_id}/alumnos", response_model=List[AlumnoSchema])
async def alumnos_por_asignatura(
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Obtener alumnos matriculados en una asignatura específica"""
    # Verificar que el docente tiene acceso a esta asignatura
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    asignatura = db.query(Asignatura).filter(
        Asignatura.id == asignatura_id,
        Asignatura.docente_id == docente.id
    ).first()
    
@router.get("/asignatura/{asignatura_id}/alumnos", response_model=List[AlumnoSchema])
async def alumnos_por_asignatura_nuevo(
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Obtener alumnos matriculados en una asignatura específica (nuevo endpoint)"""
    # Verificar que el docente tiene acceso a esta asignatura
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    asignatura = db.query(Asignatura).filter(
        Asignatura.id == asignatura_id,
        Asignatura.docente_id == docente.id
    ).first()
    
    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada o no tienes acceso a ella"
        )
    
    # Obtener alumnos matriculados usando consulta directa
    from sqlalchemy import text
    matriculas_data = db.execute(
        text("SELECT alumno_id FROM matriculas WHERE asignatura_id = :asignatura_id"),
        {"asignatura_id": asignatura_id}
    ).fetchall()
    
    alumnos = []
    for matricula in matriculas_data:
        alumno_id = matricula[0]  # El resultado es una tupla
        alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
        if alumno:
            alumnos.append(alumno)
    
    return alumnos

@router.get("/asignatura/{asignatura_id}/notas", response_model=List[NotaSchema])
async def get_notas_por_asignatura_nuevo(
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Obtener todas las notas de una asignatura específica (nuevo endpoint)"""
    # Verificar que el docente tiene acceso a esta asignatura
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    asignatura = db.query(Asignatura).filter(
        Asignatura.id == asignatura_id,
        Asignatura.docente_id == docente.id
    ).first()
    
    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada o no tienes acceso a ella"
        )
    
    # Obtener alumnos matriculados
    from sqlalchemy import text
    matriculas_data = db.execute(
        text("SELECT alumno_id FROM matriculas WHERE asignatura_id = :asignatura_id"),
        {"asignatura_id": asignatura_id}
    ).fetchall()
    
    alumno_ids = [matricula[0] for matricula in matriculas_data]
    
    # Obtener todas las notas de estos alumnos para esta asignatura
    notas = db.query(Nota).filter(
        Nota.alumno_id.in_(alumno_ids),
        Nota.asignatura_id == asignatura_id
    ).all()
    
    return notas

@router.get("/asignaturas/{asignatura_id}/notas", response_model=List[NotaSchema])
async def get_notas_por_asignatura(
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Obtener todas las notas de una asignatura específica"""
    # Verificar que el docente tiene acceso a esta asignatura
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    asignatura = db.query(Asignatura).filter(
        Asignatura.id == asignatura_id,
        Asignatura.docente_id == docente.id
    ).first()
    
    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada o no tienes acceso a ella"
        )
    
    # Obtener todas las notas de la asignatura
    notas = db.query(Nota).filter(Nota.asignatura_id == asignatura_id).all()
    return notas

@router.post("/notas", response_model=NotaSchema)
async def registrar_nota(
    nota_data: NotaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Registrar nueva nota"""
    # Verificar que el docente tiene acceso a esta asignatura
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    asignatura = db.query(Asignatura).filter(
        Asignatura.id == nota_data.asignatura_id,
        Asignatura.docente_id == docente.id
    ).first()
    
    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada o no tienes acceso a ella"
        )
    
    # Verificar que el alumno está matriculado en la asignatura
    matricula = db.execute(
        matriculas.select().where(
            matriculas.c.alumno_id == nota_data.alumno_id,
            matriculas.c.asignatura_id == nota_data.asignatura_id
        )
    ).first()
    
    if not matricula:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El alumno no está matriculado en esta asignatura"
        )
    
    # Validar calificación
    if not (0 <= nota_data.calificacion <= 20):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La calificación debe estar entre 0 y 20"
        )
    
    # Si es examen_final, hacer upsert para asegurar única nota
    if nota_data.tipo_nota == "examen_final":
        existente = db.query(Nota).filter(
            Nota.alumno_id == nota_data.alumno_id,
            Nota.asignatura_id == nota_data.asignatura_id,
            Nota.tipo_nota == "examen_final"
        ).first()
        if existente:
            existente.calificacion = nota_data.calificacion
            db.commit()
            db.refresh(existente)
            return existente

    # Crear nota
    db_nota = Nota(
        alumno_id=nota_data.alumno_id,
        asignatura_id=nota_data.asignatura_id,
        calificacion=nota_data.calificacion,
        tipo_nota=nota_data.tipo_nota
    )
    
    db.add(db_nota)
    db.commit()
    db.refresh(db_nota)
    
    return db_nota

@router.put("/notas/{nota_id}", response_model=NotaSchema)
async def actualizar_nota(
    nota_id: int,
    nota_data: NotaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Actualizar nota existente"""
    # Verificar que el docente tiene acceso a esta nota
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    nota = db.query(Nota).filter(Nota.id == nota_id).first()
    if not nota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nota no encontrada"
        )
    
    # Verificar que la asignatura pertenece al docente
    asignatura = db.query(Asignatura).filter(
        Asignatura.id == nota.asignatura_id,
        Asignatura.docente_id == docente.id
    ).first()
    
    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar esta nota"
        )
    
    # Validar calificación
    if not (0 <= nota_data.calificacion <= 20):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La calificación debe estar entre 0 y 20"
        )
    
    # Evitar duplicados si se cambia a examen_final
    if nota_data.tipo_nota == "examen_final":
        existente = db.query(Nota).filter(
            Nota.alumno_id == nota.alumno_id,
            Nota.asignatura_id == nota.asignatura_id,
            Nota.tipo_nota == "examen_final",
            Nota.id != nota_id
        ).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una nota de examen final para este alumno en esta asignatura. Edítala en lugar de crear otra."
            )

    # Actualizar nota
    nota.calificacion = nota_data.calificacion
    nota.tipo_nota = nota_data.tipo_nota
    db.commit()
    db.refresh(nota)
    
    return nota

@router.get("/asignaturas/{asignatura_id}/notas", response_model=List[NotaSchema])
async def notas_por_asignatura(
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Obtener todas las notas de una asignatura"""
    # Verificar que el docente tiene acceso a esta asignatura
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    asignatura = db.query(Asignatura).filter(
        Asignatura.id == asignatura_id,
        Asignatura.docente_id == docente.id
    ).first()
    
    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada o no tienes acceso a ella"
        )
    
    notas = db.query(Nota).filter(Nota.asignatura_id == asignatura_id).all()
    return notas

@router.delete("/notas/{nota_id}")
async def eliminar_nota(
    nota_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Eliminar nota"""
    # Verificar que el docente tiene acceso a esta nota
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    nota = db.query(Nota).filter(Nota.id == nota_id).first()
    if not nota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nota no encontrada"
        )
    
    # Verificar que la asignatura pertenece al docente
    asignatura = db.query(Asignatura).filter(
        Asignatura.id == nota.asignatura_id,
        Asignatura.docente_id == docente.id
    ).first()
    
    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar esta nota"
        )
    
    db.delete(nota)
    db.commit()
    
    return {"message": "Nota eliminada correctamente"}

@router.get("/alumnos-por-ciclo")
async def obtener_alumnos_por_ciclo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Obtener alumnos organizados por ciclo para el docente actual"""
    # Buscar el docente asociado al usuario
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    # Obtener asignaturas del docente
    asignaturas = db.query(Asignatura).filter(Asignatura.docente_id == docente.id).all()
    asignatura_ids = [asignatura.id for asignatura in asignaturas]
    
    if not asignatura_ids:
        return {"ciclos": []}
    
    # Obtener alumnos matriculados en las asignaturas del docente
    alumnos_matriculados = db.execute(
        matriculas.select().where(matriculas.c.asignatura_id.in_(asignatura_ids))
    ).fetchall()
    
    # Obtener IDs de alumnos únicos
    alumno_ids = list(set([row.alumno_id for row in alumnos_matriculados]))
    
    if not alumno_ids:
        return {"ciclos": []}
    
    # Obtener información completa de los alumnos
    alumnos = db.query(Alumno).filter(Alumno.id.in_(alumno_ids)).all()
    
    # Organizar por ciclo
    ciclos = {}
    for alumno in alumnos:
        ciclo = alumno.ciclo
        if ciclo not in ciclos:
            ciclos[ciclo] = []
        
        # Obtener asignaturas del alumno en las que enseña este docente
        asignaturas_alumno = []
        for matricula in alumnos_matriculados:
            if matricula.alumno_id == alumno.id:
                asignatura = next((a for a in asignaturas if a.id == matricula.asignatura_id), None)
                if asignatura:
                    asignaturas_alumno.append({
                        "id": asignatura.id,
                        "nombre": asignatura.nombre
                    })
        
        ciclos[ciclo].append({
            "id": alumno.id,
            "nombre_completo": alumno.nombre_completo,
            "dni": alumno.dni,
            "ciclo": alumno.ciclo,
            "email": alumno.usuario.email,
            "asignaturas": asignaturas_alumno
        })
    
    # Convertir a lista ordenada
    ciclos_lista = []
    for ciclo, alumnos_ciclo in sorted(ciclos.items()):
        ciclos_lista.append({
            "ciclo": ciclo,
            "alumnos": sorted(alumnos_ciclo, key=lambda x: x["nombre_completo"]),
            "total_alumnos": len(alumnos_ciclo)
        })
    
    return {"ciclos": ciclos_lista}

@router.put("/notas/{nota_id}/publicar")
async def publicar_nota(
    nota_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Publicar una nota para que el alumno pueda verla"""
    # Buscar la nota
    nota = db.query(Nota).filter(Nota.id == nota_id).first()
    if not nota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nota no encontrada"
        )
    
    # Verificar que el docente tiene acceso a esta asignatura
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    # Verificar que la asignatura pertenece al docente
    asignatura = db.query(Asignatura).filter(Asignatura.id == nota.asignatura_id).first()
    if not asignatura or asignatura.docente_id != docente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para publicar esta nota"
        )
    
    # Verificar si la nota ya está publicada
    if nota.publicada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta nota ya está publicada"
        )
    
    # Publicar la nota
    nota.publicada = True
    db.commit()
    db.refresh(nota)
    
    # Obtener información del alumno
    alumno = db.query(Alumno).filter(Alumno.id == nota.alumno_id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    return {
        "message": "Nota publicada exitosamente",
        "nota": {
            "id": nota.id,
            "calificacion": nota.calificacion,
            "tipo_nota": nota.tipo_nota,
            "publicada": nota.publicada,
            "alumno": {
                "nombre": alumno.nombre_completo,
                "email": alumno.usuario.email
            },
            "asignatura": asignatura.nombre
        }
    }

@router.put("/notas/{nota_id}/despublicar")
async def despublicar_nota(
    nota_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Despublicar una nota para que el alumno no pueda verla"""
    # Buscar la nota
    nota = db.query(Nota).filter(Nota.id == nota_id).first()
    if not nota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nota no encontrada"
        )
    
    # Verificar que el docente tiene acceso a esta asignatura
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    # Verificar que la asignatura pertenece al docente
    asignatura = db.query(Asignatura).filter(Asignatura.id == nota.asignatura_id).first()
    if not asignatura or asignatura.docente_id != docente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para despublicar esta nota"
        )
    
    # Verificar si la nota ya está despublicada
    if not nota.publicada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta nota ya está despublicada"
        )
    
    # Despublicar la nota
    nota.publicada = False
    db.commit()
    db.refresh(nota)
    
    # Obtener información del alumno
    alumno = db.query(Alumno).filter(Alumno.id == nota.alumno_id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    return {
        "message": "Nota despublicada exitosamente",
        "nota": {
            "id": nota.id,
            "calificacion": nota.calificacion,
            "tipo_nota": nota.tipo_nota,
            "publicada": nota.publicada,
            "alumno": {
                "nombre": alumno.nombre_completo,
                "email": alumno.usuario.email
            },
            "asignatura": asignatura.nombre
        }
    }

@router.put("/asignaturas/{asignatura_id}/publicar-todas-notas")
async def publicar_todas_notas(
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Publicar todas las notas de una asignatura específica"""
    # Verificar que el docente tiene acceso a esta asignatura
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    # Verificar que la asignatura pertenece al docente
    asignatura = db.query(Asignatura).filter(
        Asignatura.id == asignatura_id,
        Asignatura.docente_id == docente.id
    ).first()
    
    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada o no tienes acceso a ella"
        )
    
    # Obtener todas las notas no publicadas de la asignatura
    notas_no_publicadas = db.query(Nota).filter(
        Nota.asignatura_id == asignatura_id,
        Nota.publicada == False
    ).all()
    
    if not notas_no_publicadas:
        return {
            "message": "No hay notas pendientes por publicar en esta asignatura",
            "notas_publicadas": 0
        }
    
    # Publicar todas las notas
    for nota in notas_no_publicadas:
        nota.publicada = True
    
    db.commit()
    
    return {
        "message": "Todas las notas han sido publicadas exitosamente",
        "notas_publicadas": len(notas_no_publicadas),
        "asignatura": asignatura.nombre
    }

@router.post("/asignaturas/{asignatura_id}/alumnos/{alumno_id}/enviar-notas")
async def enviar_todas_las_notas(
    asignatura_id: int,
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Enviar todas las notas de un alumno en una asignatura específica por email"""
    
    # Verificar que el docente tiene acceso a esta asignatura
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    # Verificar que la asignatura pertenece al docente
    asignatura = db.query(Asignatura).filter(
        Asignatura.id == asignatura_id,
        Asignatura.docente_id == docente.id
    ).first()
    
    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada o no tienes acceso a ella"
        )
    
    # Verificar que el alumno está matriculado en la asignatura
    matricula = db.execute(
        matriculas.select().where(
            matriculas.c.alumno_id == alumno_id,
            matriculas.c.asignatura_id == asignatura_id
        )
    ).first()
    
    if not matricula:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El alumno no está matriculado en esta asignatura"
        )
    
    # Obtener información del alumno
    alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    # Verificar que el alumno tenga notas publicadas en esta asignatura
    notas = db.query(Nota).filter(
        Nota.alumno_id == alumno_id,
        Nota.asignatura_id == asignatura_id,
        Nota.publicada == True
    ).all()
    
    if not notas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El alumno no tiene notas publicadas en esta asignatura"
        )
    
    # Intentar enviar notificación por email
    try:
        from services.email_service import send_grades_published_notification
        email_result = await send_grades_published_notification(
            email=alumno.usuario.email,
            nombre_alumno=alumno.nombre_completo,
            asignatura_nombre=asignatura.nombre
        )
        
        if email_result["success"]:
            return {
                "message": "Notificación enviada exitosamente por email",
                "alumno": {
                    "id": alumno.id,
                    "nombre": alumno.nombre_completo,
                    "email": alumno.usuario.email
                },
                "asignatura": {
                    "id": asignatura.id,
                    "nombre": asignatura.nombre
                },
                "notas_publicadas": len(notas),
                "email_sent": True,
                "email_message": email_result["message"]
            }
        else:
            return {
                "message": "Error al enviar la notificación por email",
                "alumno": {
                    "id": alumno.id,
                    "nombre": alumno.nombre_completo,
                    "email": alumno.usuario.email
                },
                "asignatura": {
                    "id": asignatura.id,
                    "nombre": asignatura.nombre
                },
                "notas_publicadas": len(notas),
                "email_sent": False,
                "email_error": email_result["message"],
                "instructions": "Verifica la configuración de email en el sistema."
            }
    except Exception as e:
        return {
            "message": "Error al enviar la notificación por email",
            "alumno": {
                "id": alumno.id,
                "nombre": alumno.nombre_completo,
                "email": alumno.usuario.email
            },
            "asignatura": {
                "id": asignatura.id,
                "nombre": asignatura.nombre
            },
            "notas_publicadas": len(notas),
            "email_sent": False,
            "email_error": f"Error en el servicio de email: {str(e)}",
            "instructions": "Verifica la configuración de email en el sistema."
        }

@router.get("/reportes/{asignatura_id}/{tipo_evaluacion}")
async def obtener_reporte(
    asignatura_id: int,
    tipo_evaluacion: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Obtener reporte de notas por asignatura y tipo de evaluación usando cálculo dinámico desde notas"""
    # Verificar que el docente tiene acceso a esta asignatura
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )

    # Verificar que la asignatura pertenece al docente
    asignatura = db.query(Asignatura).filter(
        Asignatura.id == asignatura_id,
        Asignatura.docente_id == docente.id
    ).first()

    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada o no tienes acceso a ella"
        )

    # Obtener alumnos matriculados en la asignatura
    from sqlalchemy import text
    matriculas_data = db.execute(
        text("SELECT alumno_id FROM matriculas WHERE asignatura_id = :asignatura_id"),
        {"asignatura_id": asignatura_id}
    ).fetchall()

    alumno_ids = [matricula[0] for matricula in matriculas_data]

    # Normalizar tipo de evaluación solicitado
    tipo_norm = _normalize_tipo_evaluacion(tipo_evaluacion)

    # Calcular de forma dinámica desde la tabla de notas
    reporte_data = []
    for alumno_id in alumno_ids:
        alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
        if not alumno:
            continue

        # Calcular promedios dinámicamente para el alumno y asignatura
        promedios = calcular_promedios_alumno(db, alumno_id, asignatura_id)
        calificacion = promedios.get(tipo_norm, 0.0)

        reporte_data.append({
            "alumno": alumno.nombre_completo,
            "asignatura": asignatura.nombre,
            "ciclo": alumno.ciclo,
            "tipo_evaluacion": tipo_evaluacion,
            "calificacion": calificacion
        })

    return {
        "reporte": reporte_data,
        "total_alumnos": len(reporte_data),
        "asignatura": asignatura.nombre,
        "tipo_evaluacion": tipo_evaluacion
    }

@router.post("/reportes/enviar-admin")
async def enviar_reporte_admin(
    reporte_data: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Enviar reporte de notas al administrador"""
    # Verificar que el docente existe
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    # Preparar carpeta de reportes
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(backend_dir, "reports")
    try:
        os.makedirs(reports_dir, exist_ok=True)
    except Exception:
        # Si falla usar directorio actual
        reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
        os.makedirs(reports_dir, exist_ok=True)

    # Construir nombre de archivo
    asignatura = str(reporte_data.get("asignatura", "asignatura")).replace(" ", "_")
    tipo_eval = str(reporte_data.get("tipo_evaluacion", "evaluacion")).replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_{docente.id}_{asignatura}_{tipo_eval}_{timestamp}.csv"

    # Generar CSV en memoria
    columnas = ["alumno", "ciclo", "asignatura", "tipo_evaluacion", "calificacion"]
    try:
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=columnas)
        writer.writeheader()
        for fila in reporte_data.get("reporte", []):
            writer.writerow({
                "alumno": fila.get("alumno", ""),
                "ciclo": fila.get("ciclo", ""),
                "asignatura": fila.get("asignatura", asignatura),
                "tipo_evaluacion": fila.get("tipo_evaluacion", tipo_eval),
                "calificacion": fila.get("calificacion", "")
            })
        csv_bytes = buffer.getvalue().encode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo generar el archivo de reporte en memoria: {e}")

    # Guardar registro del reporte (indicando que el archivo está en BD)
    reporte_record = ReporteDocente(
        docente_id=docente.id,
        nombre_docente=docente.nombre_completo,
        asignatura=reporte_data.get("asignatura", ""),
        tipo_evaluacion=reporte_data.get("tipo_evaluacion", ""),
        archivo_path=f"db:{filename}"
    )
    db.add(reporte_record)
    db.commit()
    db.refresh(reporte_record)

    # Guardar contenido del archivo en la tabla de archivos
    archivo_record = ReporteArchivoDocente(
        reporte_id=reporte_record.id,
        filename=filename,
        mime_type="text/csv",
        content=csv_bytes
    )
    db.add(archivo_record)
    db.commit()
    db.refresh(archivo_record)

    return {
        "message": "Reporte enviado al administrador exitosamente",
        "docente": docente.nombre_completo,
        "reporte_id": reporte_record.id,
        "archivo": filename,
        "fecha_envio": str(datetime.now())
    }

@router.post("/reportes/enviar-email")
async def enviar_reporte_email(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Generar el PDF del reporte y enviarlo por correo a la dirección indicada.

    Espera un payload con:
    - email/correo: str (se acepta cualquiera de las dos claves)
    - asignatura: str
    - tipo_evaluacion: str
    - reporte: lista de filas con keys: alumno, ciclo, asignatura, tipo_evaluacion, calificacion
    """
    # Verificar que el docente existe
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )

    # Aceptar distintas claves desde el frontend: "email" o "correo"
    email = payload.get("email") or payload.get("correo") or payload.get("destinatario")
    # Normalizar y validar de forma tolerante
    if not email:
        raise HTTPException(status_code=400, detail="Email requerido")
    email = str(email).strip()
    # Evitar validación estricta que puede fallar por espacios u otros caracteres
    # Usar una validación sencilla para permitir correos válidos típicos
    import re
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        raise HTTPException(status_code=400, detail="Email inválido")

    # Construir nombre de archivo (PDF)
    asignatura = str(payload.get("asignatura", "asignatura")).replace(" ", "_")
    tipo_eval = str(payload.get("tipo_evaluacion", "evaluacion")).replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_{docente.id}_{asignatura}_{tipo_eval}_{timestamp}.pdf"

    # Generar PDF con los datos del reporte en memoria
    try:
        styles = getSampleStyleSheet()
        story = []

        # Encabezado unificado
        from models import ConfiguracionSistema
        config = db.query(ConfiguracionSistema).first()
        titulo_bar = (config.nombre_sistema if config and config.nombre_sistema else "Sistema de Notas")
        subtitulo_bar = f"Reporte: {payload.get('tipo_evaluacion', tipo_eval)} - {payload.get('asignatura', asignatura)}"
        story.append(build_header(titulo_bar, subtitulo_bar, logo_url=(config.logo_url if config else None)))
        story.append(Spacer(1, 4))

        # Estilos personalizados para centrado y encabezado informativo alineado a la izquierda
        title_style = ParagraphStyle('TitleCentered', parent=styles['Title'], alignment=TA_CENTER)
        info_style = ParagraphStyle('InfoLeft', parent=styles['Normal'], alignment=TA_LEFT)

        # Información del encabezado
        story.append(Paragraph(f"Docente: {docente.nombre_completo}", info_style))
        story.append(Paragraph(f"Asignatura: {payload.get('asignatura', asignatura)}", info_style))
        story.append(Paragraph(f"Tipo evaluación: {payload.get('tipo_evaluacion', tipo_eval)}", info_style))
        story.append(Paragraph(f"Fecha envío: {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_style))
        story.append(build_separator())
        story.append(Spacer(1, 6))
        titulo = f"Reporte de Notas - {payload.get('asignatura', asignatura)} ({payload.get('tipo_evaluacion', tipo_eval)})"
        story.append(Paragraph(titulo, title_style))
        story.append(Spacer(1, 12))

        # Encabezados y filas
        encabezados = ["Alumno", "Ciclo", "Asignatura", "Tipo Evaluación", "Calificación"]
        filas = []
        for fila in payload.get("reporte", []):
            filas.append([
                str(fila.get("alumno", "")),
                str(fila.get("ciclo", "")),
                str(fila.get("asignatura", payload.get("asignatura", asignatura))),
                str(fila.get("tipo_evaluacion", payload.get("tipo_evaluacion", tipo_eval))),
                str(fila.get("calificacion", "")),
            ])

        data = [encabezados] + (filas if filas else [["-","-","-","-","-"]])
        table = Table(data, repeatRows=1)
        apply_table_style(table)
        story.append(table)

        # Construir el PDF en memoria
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo generar el PDF del reporte: {e}")

    # Enviar correo con adjunto (bytes en memoria)
    try:
        from services.email_service import send_report_with_attachment_bytes
        email_result = await send_report_with_attachment_bytes(
            email=email,
            nombre_docente=docente.nombre_completo,
            asignatura=payload.get("asignatura", asignatura),
            tipo_evaluacion=payload.get("tipo_evaluacion", tipo_eval),
            filename=filename,
            file_bytes=pdf_bytes,
            mime_type="application/pdf",
        )
        if not email_result.get("success", False):
            raise HTTPException(status_code=500, detail=email_result.get("message", "No se pudo enviar el correo"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo enviar el correo: {e}")

    # Persistir registro en DB y archivo del reporte en BD
    reporte_record = ReporteDocente(
        docente_id=docente.id,
        nombre_docente=docente.nombre_completo,
        asignatura=payload.get("asignatura", ""),
        tipo_evaluacion=payload.get("tipo_evaluacion", ""),
        archivo_path=f"db:{filename}",
    )
    db.add(reporte_record)
    db.commit()
    db.refresh(reporte_record)

    archivo_record = ReporteArchivoDocente(
        reporte_id=reporte_record.id,
        filename=filename,
        mime_type="application/pdf",
        content=pdf_bytes,
    )
    db.add(archivo_record)
    db.commit()

    return {
        "message": email_result.get("message", "Reporte enviado"),
        "success": email_result.get("success", False),
        "docente": docente.nombre_completo,
        "reporte_id": reporte_record.id,
        "archivo": filename,
        "email": email,
        "fecha_envio": str(datetime.now())
    }

@router.get("/asignatura/{asignatura_id}/promedios", response_model=List[Dict[str, Any]])
async def obtener_promedios_asignatura(
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Obtener todos los promedios de una asignatura calculados dinámicamente desde las notas"""
    try:
        # Verificar que el docente tiene acceso a esta asignatura
        docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
        if not docente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Docente no encontrado"
            )
        
        # Verificar que la asignatura pertenece al docente
        asignatura = db.query(Asignatura).filter(
            Asignatura.id == asignatura_id,
            Asignatura.docente_id == docente.id
        ).first()
        
        if not asignatura:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignatura no encontrada o no tienes acceso a ella"
            )
        
        # Calcular promedios dinámicamente usando el helper
        promedios_data = calcular_promedios_asignatura(db, asignatura_id)
        
        return promedios_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener promedios: {str(e)}"
        )
        
        return promedios_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener promedios: {str(e)}"
        )
@router.put("/mi-perfil")
async def actualizar_mi_perfil(
    perfil_data: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("docente"))
):
    """Actualizar el perfil del docente (contraseña)"""
    # Obtener el docente
    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    # Verificar que se proporcionó la contraseña actual
    password_actual = perfil_data.get("password_actual")
    if not password_actual:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es requerida"
        )
    
    # Verificar la contraseña actual
    if not verify_password(password_actual, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta"
        )
    
    # Verificar que se proporcionó la nueva contraseña
    nueva_password = perfil_data.get("nueva_password")
    if not nueva_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña es requerida"
        )
    
    # Verificar que la nueva contraseña tiene al menos 6 caracteres
    if len(nueva_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 6 caracteres"
        )
    
    # Actualizar la contraseña
    current_user.password_hash = get_password_hash(nueva_password)
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Contraseña actualizada exitosamente",
        "docente": {
            "id": docente.id,
            "nombre_completo": docente.nombre_completo,
            "email": current_user.email
        }
    }

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Usuario, Docente, Asignatura, Alumno, Nota, matriculas
from schemas import (
    Asignatura as AsignaturaSchema,
    Alumno as AlumnoSchema,
    NotaCreate, NotaUpdate, Nota as NotaSchema
)
from auth import require_role, verify_password, get_password_hash

router = APIRouter()

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
        from email_config import send_grades_published_notification
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

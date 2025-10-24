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
import os
import re
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from fastapi import Depends
from promedio_calculator import calcular_promedios_alumno

router = APIRouter()

# Nota mínima para considerar una asignatura aprobada (valor por defecto 11)
PASSING_GRADE = int(os.getenv("PASSING_GRADE", "11"))


def get_next_cycle(ciclo: str) -> str:
    """Intentar calcular el siguiente ciclo a partir de la cadena del ciclo actual.

    Suposiciones:
    - El campo `ciclo` contiene algún número representando el nivel/ciclo (por ejemplo "Ciclo 1", "1", "Nivel 2").
    - Si no se encuentra un número, se lanza ValueError y no se realiza la matrícula automática.
    """
    text = str(ciclo).strip()
    # 1) Intentar encontrar un número arábigo
    m = re.search(r"(\d+)(?!.*\d)", text)
    if m:
        current = int(m.group(1))
        next_cycle = current + 1
        next_ciclo_str = re.sub(r"(\d+)(?!.*\d)", str(next_cycle), text, count=1)
        return next_ciclo_str

    # 2) Intentar detectar numerales romanos (I, II, III, IV, V, VI, ...)
    roman_map = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
        'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10
    }
    m2 = re.search(r"\b(I|II|III|IV|V|VI|VII|VIII|IX|X)\b", text, flags=re.IGNORECASE)
    if m2:
        roman = m2.group(1).upper()
        current = roman_map.get(roman)
        if not current:
            raise ValueError("No se pudo determinar el siguiente ciclo (roman not supported)")
        next_num = current + 1
        # convertir next_num a romano ( sencillo hasta 10 )
        inv_map = {v: k for k, v in roman_map.items()}
        next_roman = inv_map.get(next_num, str(next_num))
        next_ciclo_str = re.sub(r"\b(I|II|III|IV|V|VI|VII|VIII|IX|X)\b", next_roman, text, count=1, flags=re.IGNORECASE)
        return next_ciclo_str

    # Si no pudimos inferir nada, lanzar error para que el llamador lo maneje
    raise ValueError("No se pudo determinar el siguiente ciclo a partir del valor de 'ciclo'.")

# Helper para extraer el ciclo base sin sección
def get_base_ciclo(ciclo: str) -> str:
    text = str(ciclo).strip()
    m2 = re.search(r"\b(I|II|III|IV|V|VI|VII|VIII|IX|X)\b", text, flags=re.IGNORECASE)
    if m2:
        return m2.group(1).upper()
    m = re.search(r"(\d+)(?!.*\d)", text)
    if m:
        return m.group(1)
    return text


def alumno_aprobo_asignatura(db: Session, alumno_id: int, asignatura_id: int) -> bool:
    """Determina si el alumno aprobó una asignatura: existe al menos una nota publicada >= PASSING_GRADE."""
    notas = db.query(Nota).filter(
        Nota.alumno_id == alumno_id,
        Nota.asignatura_id == asignatura_id,
        Nota.publicada == True
    ).all()
    if not notas:
        return False
    # Consideramos aprobada si la máxima nota publicada es >= PASSING_GRADE
    return max(n.calificacion for n in notas) >= PASSING_GRADE


def matricular_alumno_en_siguiente_ciclo(db: Session, alumno: Alumno) -> dict:
    """Verifica si el alumno aprobó todas las asignaturas del ciclo actual. Si es así,
    registra (actualiza) su campo `ciclo` al siguiente ciclo sin matricular automáticamente en asignaturas.

    Retorna un dict con el resultado y detalles.
    """
    resultado = {"alumno_id": alumno.id, "nombre": alumno.nombre_completo, "matriculado": False, "mensaje": ""}
    try:
        next_ciclo = get_next_cycle(alumno.ciclo)
    except ValueError as e:
        resultado["mensaje"] = str(e)
        return resultado

    # Obtener asignaturas del ciclo actual en las que el alumno está matriculado
    matriculas_data = db.execute(
        matriculas.select().where(matriculas.c.alumno_id == alumno.id)
    ).fetchall()

    asignaturas_actuales_ids = [m.asignatura_id for m in matriculas_data]
    # Filtrar sólo aquellas asignaturas que pertenecen al ciclo del alumno
    asignaturas_actuales = db.query(Asignatura).filter(
        Asignatura.id.in_(asignaturas_actuales_ids),
        Asignatura.ciclo == get_base_ciclo(alumno.ciclo)
    ).all()

    # Si no tiene asignaturas en el ciclo actual, no se puede avanzar
    if not asignaturas_actuales:
        resultado["mensaje"] = "No se encontraron asignaturas del ciclo actual para evaluar."
        return resultado

    # Verificar aprobación de cada asignatura
    for asign in asignaturas_actuales:
        if not alumno_aprobo_asignatura(db, alumno.id, asign.id):
            resultado["mensaje"] = f"No aprobó la asignatura: {asign.nombre} (id={asign.id})."
            return resultado

    # Si llegó aquí, aprobó todas las asignaturas del ciclo actual
    # Buscar asignaturas del siguiente ciclo
    asignaturas_siguiente = db.query(Asignatura).filter(Asignatura.ciclo == get_base_ciclo(next_ciclo)).all()
    # Actualizamos el campo ciclo del alumno para registrar que pasó al siguiente ciclo.
    alumno.ciclo = next_ciclo
    db.commit()

    # No crear matrículas automáticas: solo informar las asignaturas disponibles en el siguiente ciclo
    asignaturas_siguiente_ids = [a.id for a in asignaturas_siguiente]
    resultado["matriculado"] = False
    resultado["registrado"] = True
    resultado["asignaturas_siguiente_ids"] = asignaturas_siguiente_ids
    if asignaturas_siguiente_ids:
        resultado["mensaje"] = f"Registrado en el siguiente ciclo ({next_ciclo}). Existen {len(asignaturas_siguiente_ids)} asignaturas disponibles en ese ciclo."
    else:
        resultado["mensaje"] = f"Registrado en el siguiente ciclo ({next_ciclo}). No hay asignaturas definidas para ese ciclo."

    return resultado


@router.post("/matricula-automatica")
async def matricula_automatica(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("alumno"))
):
    """Endpoint que verifica si el alumno actual puede ser matriculado automáticamente al siguiente ciclo.

    - Si el alumno aprobó todas las asignaturas de su ciclo actual, se le matricula en las asignaturas del siguiente ciclo.
    - Retorna el resultado de la operación.
    """
    alumno = db.query(Alumno).filter(Alumno.usuario_id == current_user.id).first()
    if not alumno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado")

    # Ejecutar la matrícula en background para no bloquear la petición (pero esperamos el resultado aquí para devolverlo)
    # Dado que la operación es rápida, la ejecutamos directamente y retornamos el resultado.
    resultado = matricular_alumno_en_siguiente_ciclo(db, alumno)
    return resultado



# Esquema para cambiar contraseña
class CambiarContrasenaRequest(BaseModel):
    contrasena_actual: str
    nueva_contrasena: str

@router.get("/mis-asignaturas", response_model=List[AsignaturaSchema])
async def mis_asignaturas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("alumno")),
    solo_ciclo_actual: bool = True
):
    """Obtener asignaturas matriculadas del alumno actual
    
    Por defecto, solo devuelve las asignaturas del ciclo actual.
    Si solo_ciclo_actual=False, devuelve todas las asignaturas matriculadas.
    """
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
            # Filtrar solo por asignaturas del ciclo actual si se solicita
            if not solo_ciclo_actual or asignatura.ciclo == get_base_ciclo(alumno.ciclo):
                asignaturas.append(asignatura)
    
    return asignaturas

@router.get("/mis-notas", response_model=List[NotaSchema])
async def mis_notas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("alumno")),
    solo_ciclo_actual: bool = True
):
    """Obtener todas las notas del alumno actual"""
    # Buscar el alumno asociado al usuario
    alumno = db.query(Alumno).filter(Alumno.usuario_id == current_user.id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    query = db.query(Nota).filter(Nota.alumno_id == alumno.id, Nota.publicada == True)
    
    if solo_ciclo_actual:
        # Filtrar por asignaturas del ciclo actual
        query = query.join(Asignatura, Nota.asignatura_id == Asignatura.id).filter(
            Asignatura.ciclo == get_base_ciclo(alumno.ciclo)
        )
    
    notas = query.all()
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
    current_user: Usuario = Depends(require_role("alumno")),
    solo_ciclo_actual: bool = True
):
    """Calcular promedio por asignatura del alumno"""
    alumno = db.query(Alumno).filter(Alumno.usuario_id == current_user.id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )

    matriculas_data = db.execute(
        matriculas.select().where(matriculas.c.alumno_id == alumno.id)
    ).fetchall()

    resultados = []
    base_ciclo = get_base_ciclo(alumno.ciclo)

    for matricula in matriculas_data:
        asignatura = db.query(Asignatura).filter(Asignatura.id == matricula.asignatura_id).first()
        if asignatura:
            # Filtrar por ciclo actual si se solicita
            if solo_ciclo_actual and asignatura.ciclo != base_ciclo:
                continue

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

@router.get("/promedio-por-asignatura/pdf")
async def promedio_por_asignatura_pdf(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("alumno")),
    solo_ciclo_actual: bool = True
):
    """Generar y descargar PDF con promedios por asignatura del alumno actual.

    Usa las notas publicadas para calcular promedios si no hay registros en `Promedio`.
    Incluye columnas: Asignatura, Total Notas, Promedio, Nota Máxima y Nota Mínima.
    """
    import io
    from datetime import datetime
    from fastapi.responses import StreamingResponse
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from pdf_style import build_header, apply_table_style, build_separator

    # Buscar el alumno asociado al usuario
    alumno = db.query(Alumno).filter(Alumno.usuario_id == current_user.id).first()
    if not alumno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado")

    # Obtener asignaturas matriculadas
    matriculas_data = db.execute(
        matriculas.select().where(matriculas.c.alumno_id == alumno.id)
    ).fetchall()

    resultados = []

    base_ciclo = get_base_ciclo(alumno.ciclo)

    for matricula in matriculas_data:
        asignatura = db.query(Asignatura).filter(Asignatura.id == matricula.asignatura_id).first()
        if not asignatura:
            continue
        if solo_ciclo_actual and asignatura.ciclo != base_ciclo:
            continue

        # Calcular promedios dinámicamente usando el helper
        promedios_alumno = calcular_promedios_alumno(db, alumno.id, asignatura.id)
        
        if promedios_alumno:
            # Asegurar que el promedio_final sea numérico; si viene None, usar 0.0
            pf_val = promedios_alumno.get("promedio_final")
            try:
                promedio_final = float(pf_val) if pf_val is not None else 0.0
            except (TypeError, ValueError):
                promedio_final = 0.0
            # Obtener notas para estadísticas adicionales
            notas = db.query(Nota).filter(
                Nota.alumno_id == alumno.id,
                Nota.asignatura_id == asignatura.id,
                Nota.publicada == True
            ).all()
            
            if notas:
                total_notas = len([n for n in notas if n.calificacion is not None])
                nota_max = max(n.calificacion for n in notas if n.calificacion is not None) if total_notas > 0 else 0
                nota_min = min(n.calificacion for n in notas if n.calificacion is not None) if total_notas > 0 else 0
            else:
                total_notas = 0
                nota_max = 0
                nota_min = 0
        else:
            promedio_final = 0.0
            total_notas = 0
            nota_max = 0
            nota_min = 0

        resultados.append({
            "asignatura": asignatura.nombre,
            "total_notas": total_notas,
            "promedio": round(promedio_final, 2),
            "nota_maxima": nota_max,
            "nota_minima": nota_min,
            "ciclo": asignatura.ciclo
        })

    # Generar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    story = []
    title_style = ParagraphStyle('TitleCentered', parent=styles['Title'], alignment=TA_CENTER)
    info_style = ParagraphStyle('InfoJustified', parent=styles['Normal'], alignment=TA_JUSTIFY)
    # Configuración del sistema para título y logo
    from models import ConfiguracionSistema
    config = db.query(ConfiguracionSistema).first()
    system_title = (config.nombre_sistema if config and config.nombre_sistema else 'Sistema de Notas')
    system_logo = (config.logo_url if config else None)
    story.append(build_header(system_title, 'Promedios por Asignatura', logo_url=system_logo))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f'Alumno: {alumno.nombre_completo}', info_style))
    story.append(Paragraph(f'Ciclo actual: {base_ciclo}', info_style))
    story.append(Paragraph(f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}', info_style))
    story.append(build_separator())
    story.append(Spacer(1, 6))
    story.append(Paragraph('Promedios por Asignatura', title_style))
    story.append(Spacer(1, 12))

    data = [["Asignatura", "Total Notas", "Promedio", "Nota Máxima", "Nota Mínima", "Ciclo"]]
    for r in resultados:
        data.append([
            r["asignatura"],
            str(r["total_notas"]),
            f"{float(r['promedio']):.2f}",
            str(r["nota_maxima"]),
            str(r["nota_minima"]),
            str(r["ciclo"])
        ])

    table = Table(data, hAlign="LEFT")
    apply_table_style(table)

    story.append(table)
    doc.build(story)

    pdf_value = buffer.getvalue()
    buffer.close()

    # Nombre de archivo seguro
    def slugify(value: str) -> str:
        import re
        value = re.sub(r"[^a-zA-Z0-9_\-]", "_", value)
        return value.strip('_')

    filename = f"promedios_por_asignatura_{slugify(alumno.nombre_completo.lower())}.pdf"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }
    return StreamingResponse(io.BytesIO(pdf_value), media_type="application/pdf", headers=headers)

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

@router.get("/asignaturas/{asignatura_id}/resumen-pdf")
async def resumen_pdf_asignatura(
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("alumno"))
):
    """Generar y descargar PDF con resumen de promedios por asignatura.

    Incluye: actividades, prácticas, parciales, examen final, promedio final,
    además del nombre del docente, la asignatura y el ciclo.
    """
    import io
    from datetime import datetime
    from fastapi.responses import StreamingResponse
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from pdf_style import build_header, apply_table_style, build_separator

    # Buscar alumno
    alumno = db.query(Alumno).filter(Alumno.usuario_id == current_user.id).first()
    if not alumno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado")

    # Verificar matrícula en la asignatura
    matricula = db.execute(
        matriculas.select().where(
            matriculas.c.alumno_id == alumno.id,
            matriculas.c.asignatura_id == asignatura_id
        )
    ).first()
    if not matricula:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No estás matriculado en esta asignatura")

    asignatura = db.query(Asignatura).filter(Asignatura.id == asignatura_id).first()
    if not asignatura:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignatura no encontrada")

    # Obtener notas publicadas (opcional)
    notas = db.query(Nota).filter(
        Nota.alumno_id == alumno.id,
        Nota.asignatura_id == asignatura_id,
        Nota.publicada == True
    ).all()

    # Calcular promedios dinámicamente desde las notas (más robusto)
    promedios = calcular_promedios_alumno(db, alumno.id, asignatura_id)

    actividades = promedios.get("actividades")
    practicas = promedios.get("practicas")
    parciales = promedios.get("parciales")
    examen_final = promedios.get("examen_final")

    def safe(v):
        return float(v) if v is not None else 0.0

    # Usar promedio_final del helper si está disponible; de lo contrario calcular con componentes presentes
    promedio_final = promedios.get("promedio_final")
    if promedio_final is None:
        promedio_final = round(
            (safe(actividades) + safe(practicas) + safe(parciales) + safe(examen_final)) / 4.0, 2
        )

    # Generar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    story = []
    title_style = ParagraphStyle('TitleCentered', parent=styles['Title'], alignment=TA_CENTER)
    info_style = ParagraphStyle('InfoJustified', parent=styles['Normal'], alignment=TA_JUSTIFY)
    # Configuración del sistema para título y logo
    from models import ConfiguracionSistema
    config = db.query(ConfiguracionSistema).first()
    system_title = (config.nombre_sistema if config and config.nombre_sistema else 'Sistema de Notas')
    system_logo = (config.logo_url if config else None)
    story.append(build_header(system_title, 'Resumen de Promedios', logo_url=system_logo))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f'Alumno: {alumno.nombre_completo}', info_style))
    story.append(Paragraph(f'Asignatura: {asignatura.nombre}', info_style))
    docente_nombre = asignatura.docente.nombre_completo if asignatura.docente else '—'
    story.append(Paragraph(f'Docente: {docente_nombre}', info_style))
    story.append(Paragraph(f'Ciclo: {asignatura.ciclo}', info_style))
    story.append(Paragraph(f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}', info_style))
    story.append(build_separator())
    story.append(Spacer(1, 6))
    story.append(Paragraph('Resumen de Promedios', title_style))
    story.append(Spacer(1, 12))

    data = [
        ["Tipo de Evaluación", "Promedio"],
        ["Actividades", f"{safe(actividades):.2f}"],
        ["Prácticas", f"{safe(practicas):.2f}"],
        ["Parciales", f"{safe(parciales):.2f}"],
        ["Examen Final", f"{safe(examen_final):.2f}"],
        ["Promedio Final", f"{safe(promedio_final):.2f}"],
    ]
    table = Table(data, hAlign="LEFT")
    apply_table_style(table)
    story.append(table)

    doc.build(story)
    buffer.seek(0)

    filename_safe = re.sub(r"\s+", "_", asignatura.nombre.lower())
    headers = {
        "Content-Disposition": f'attachment; filename="resumen_notas_{filename_safe}.pdf"'
    }
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)

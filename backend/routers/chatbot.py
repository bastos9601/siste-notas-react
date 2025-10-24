from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Optional
from auth import require_role
import os
from dotenv import load_dotenv
from sqlalchemy import func

# Asegurar carga de variables de entorno desde backend/.env
load_dotenv()

try:
    from groq import Groq
except Exception:
    Groq = None

# Nuevas dependencias para consultas de datos
from sqlalchemy.orm import Session
from database import get_db
from models import Docente, Asignatura, Alumno, Nota, matriculas, ReporteDocente, HistorialAcademico, AsignaturaHistorial
from promedio_calculator import calcular_promedios_alumno

router = APIRouter()

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.2
    model: Optional[str] = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

ROLE_SYSTEM_PROMPTS: Dict[str, str] = {
    "admin": (
        "Eres el asistente del Sistema de Gestión de Notas para un Administrador. "
        "Ayudas a gestionar docentes, alumnos, asignaturas, matrículas, notas y reportes. "
        "Responde de forma concisa, orientada a acciones en el panel y API disponibles. "
        "Nunca inventes datos; guía cómo obtenerlos mediante las rutas y funcionalidades actuales."
    ),
    "docente": (
        "Eres el asistente del Sistema de Gestión de Notas para un Docente. "
        "Ayudas a registrar, actualizar y publicar notas, y generar reportes por asignatura y ciclo. "
        "Sugiere pasos claros según las pantallas del panel docente. No inventes datos."
    ),
    "alumno": (
        "Eres el asistente del Sistema de Gestión de Notas para un Alumno. "
        "Ayudas a consultar asignaturas, notas, promedios e historial académico, y entender calificaciones. "
        "Responde en lenguaje claro y directo, sin inventar información."
    ),
}


def _chat_with_groq(system_prompt: str, req: ChatRequest) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="GROQ_API_KEY no configurado en backend/.env")
    if Groq is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SDK de Groq no disponible. Ejecute 'pip install -r requirements.txt' y reinicie el servidor.")

    try:
        client = Groq(api_key=api_key)

        # Construir mensajes para el modelo
        groq_messages = [{"role": "system", "content": system_prompt}]
        for m in req.messages:
            role = m.role if m.role in ("user", "assistant") else "user"
            groq_messages.append({"role": role, "content": m.content})

        completion = client.chat.completions.create(
            model=req.model,
            messages=groq_messages,
            temperature=req.temperature,
        )

        return completion.choices[0].message.content
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Chatbot] Error al invocar Groq: {e}")
        raise HTTPException(status_code=502, detail=f"Error al consultar el proveedor de IA: {str(e)}")


# --- Utilidades comunes ---

def _extraer_ultimo_mensaje_usuario(req: ChatRequest) -> str:
    for m in reversed(req.messages):
        if (m.role or "user").lower() == "user":
            return m.content or ""
    return req.messages[-1].content if req.messages else ""


def _normalizar_texto_basico(s: str) -> str:
    import re
    t = (s or "").strip().lower()
    t = re.sub(r"[\.,!;:¿?¡]+", "", t)
    return t


# --- Integración de respuestas basadas en datos para ADMIN ---

def _responder_intentos_admin(texto: str, db: Session, current_user) -> Optional[str]:
    t = _normalizar_texto_basico(texto)

    # Saludo exacto "hola" con rol
    if t == "hola":
        rol = (getattr(current_user, "rol", "").strip().lower() or "admin")
        rol_str = "Administrador" if rol == "admin" else rol.capitalize() if rol else "Usuario"
        nombre_usuario = getattr(current_user, "nombre", None) or getattr(current_user, "email", None) or "usuario"
        return f"Hola {nombre_usuario}! ({rol_str})"

    # Conteos del sistema: docentes, alumnos, matriculados y asignaturas
    count_keywords = [
        "cuantos", "cuántos", "cuanto", "cuánto", "numero", "número",
        "cantidad", "total", "cuantas", "cuántas", "hay"
    ]
    parts = []

    # Docentes
    if ("docentes" in t and any(k in t for k in count_keywords)):
        parts.append(f"Docentes: {db.query(Docente).count()}")

    # Alumnos (evitar confundir con matriculados)
    if ("alumnos" in t and any(k in t for k in count_keywords) and "matricul" not in t):
        parts.append(f"Alumnos: {db.query(Alumno).count()}")

    # Alumnos matriculados (distintos alumno_id en la tabla de matrículas)
    if ("matricul" in t and any(k in t for k in count_keywords)) or ("alumnos matriculados" in t):
        rows = db.execute(matriculas.select()).fetchall()
        num_matriculados = len({r.alumno_id for r in rows})
        parts.append(f"Alumnos matriculados: {num_matriculados}")

    # Asignaturas
    if ("asignaturas" in t and any(k in t for k in count_keywords)):
        parts.append(f"Asignaturas: {db.query(Asignatura).count()}")

    if parts:
        return "En el sistema: " + "; ".join(parts) + "."

    # Docentes que enviaron reportes
    patrones_docentes_con_reportes = [
        "que docente envio reportes", "qué docente envio reportes", "qué docente envió reportes",
        "docentes que enviaron reportes", "docentes con reportes", "listar docentes con reportes",
        "quien envio reportes", "quién envio reportes", "quién envió reportes",
        "quienes enviaron reportes", "quiénes enviaron reportes",
        "docentes que enviaron reporte", "quien envio reporte", "quién envió reporte"
    ]
    if any(p in t for p in patrones_docentes_con_reportes) or (
        "reporte" in t and "docente" in t and ("envio" in t or "envió" in t or "enviaron" in t or "enviado" in t)
    ):
        # Filtro temporal opcional
        label = ""
        q = db.query(ReporteDocente)
        if "hoy" in t:
            from datetime import datetime
            inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            q = q.filter(ReporteDocente.fecha_envio >= inicio)
            label = " (hoy)"
        elif "este mes" in t:
            from datetime import datetime
            inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            q = q.filter(ReporteDocente.fecha_envio >= inicio_mes)
            label = " (este mes)"
    
        # Filtro por asignatura (opcional)
        asig_nombre = None
        for clave in ["de asignatura ", "en asignatura ", "asignatura "]:
            if clave in t:
                asig_nombre = t.split(clave, 1)[1].strip()
                break
        if asig_nombre is None and "reportes de " in t:
            cand = t.split("reportes de ", 1)[1].strip()
            stop_prefixes = ["docente", "docentes", "alumno", "alumnos", "hoy", "este mes", "cantidad", "numero", "número", "cuantos", "cuántos", "tipo", "evaluacion", "evaluación"]
            if not any(cand.startswith(sp) for sp in stop_prefixes):
                asig_nombre = cand
        if asig_nombre:
            q = q.filter(ReporteDocente.asignatura.ilike(f"%{asig_nombre}%"))
            label += " - asignatura: " + asig_nombre
    
        # Filtro por tipo de evaluación (opcional)
        tipo_nombre = None
        for clave in ["tipo evaluacion ", "tipo evaluación ", "tipo de ", "tipo "]:
            if clave in t:
                tipo_nombre = t.split(clave, 1)[1].strip()
                break
        if tipo_nombre:
            q = q.filter(ReporteDocente.tipo_evaluacion.ilike(f"%{tipo_nombre}%"))
            label += " - tipo: " + tipo_nombre
    
        # ¿Se pidió el top: docente con más reportes?
        quiere_top = any(k in t for k in [
            "docente con mas reportes", "docente con más reportes",
            "quien tiene mas reportes", "quién tiene más reportes",
            "top reportes", "mayor cantidad de reportes"
        ])
        if quiere_top:
            rows = q.with_entities(ReporteDocente.docente_id, func.count(ReporteDocente.id)).group_by(ReporteDocente.docente_id).order_by(func.count(ReporteDocente.id).desc()).all()
            if not rows:
                return "No hay reportes enviados por docentes" + label + "."
            did, cnt = rows[0]
            nombre = None
            if did is not None:
                d = db.query(Docente).filter(Docente.id == did).first()
                if d:
                    nombre = d.nombre_completo
            if not nombre:
                rep = q.first()
                nombre = rep.nombre_docente if rep and rep.nombre_docente else "Docente"
            return f"Docente con más reportes{label}: {nombre} ({cnt})."
    
        # ¿Se pidió conteo por docente?
        quiere_conteo = any(k in t for k in ["cuantos", "cuántos", "cantidad", "numero", "número"]) and "reporte" in t
        if quiere_conteo:
            rows = q.with_entities(ReporteDocente.docente_id, func.count(ReporteDocente.id)).group_by(ReporteDocente.docente_id).order_by(func.count(ReporteDocente.id).desc()).all()
            if not rows:
                return "No hay reportes enviados por docentes" + label + "."
            ids = [r[0] for r in rows if r[0] is not None]
            docentes = db.query(Docente).filter(Docente.id.in_(ids)).all() if ids else []
            name_by_id = {d.id: d.nombre_completo for d in docentes}
            partes = []
            for did, cnt in rows:
                nombre = name_by_id.get(did)
                if not nombre:
                    rep = q.filter(ReporteDocente.docente_id == did).first()
                    nombre = rep.nombre_docente if rep and rep.nombre_docente else "Docente"
                partes.append(f"{nombre} ({cnt})")
            return "Docentes con reportes" + label + ": " + ", ".join(partes) + "."
        else:
            ids = [row[0] for row in q.with_entities(ReporteDocente.docente_id).distinct().all()]
            if not ids:
                # respaldo: nombres en reportes
                nombres_rep = {row[0] for row in q.with_entities(ReporteDocente.nombre_docente).all() if row[0]}
                if not nombres_rep:
                    return "No hay reportes enviados por docentes" + label + "."
                return "Docentes que enviaron reportes" + label + ": " + ", ".join(sorted(nombres_rep)) + "."
            docentes = db.query(Docente).filter(Docente.id.in_(ids)).all()
            if not docentes:
                nombres_rep = {row[0] for row in q.with_entities(ReporteDocente.nombre_docente).all() if row[0]}
                if not nombres_rep:
                    return "No hay reportes enviados por docentes" + label + "."
                return "Docentes que enviaron reportes" + label + ": " + ", ".join(sorted(nombres_rep)) + "."
            nombres = ", ".join(d.nombre_completo for d in docentes)
            return f"Docentes que enviaron reportes{label}: {nombres}."
        # Respaldo: usar nombres guardados en los reportes
        nombres_rep = {row[0] for row in db.query(ReporteDocente.nombre_docente).all() if row[0]}
        if not nombres_rep:
            return "No hay reportes enviados por docentes."
        return "Docentes que enviaron reportes: " + ", ".join(sorted(nombres_rep)) + "."

    # Docentes sin asignaturas
    patrones_docentes_sin_asignaturas = [
        "docentes sin asignaturas",
        "docentes sin materias",
        "docentes sin cursos",
        "docentes que no tienen asignaturas",
        "que docentes no tienen asignaturas",
        "qué docentes no tienen asignaturas",
        "docentes sin asignatura"
    ]
    if any(p in t for p in patrones_docentes_sin_asignaturas):
        docentes = db.query(Docente).filter(~Docente.asignaturas.any()).all()
        if not docentes:
            return "Todos los docentes tienen asignaturas asignadas."
        nombres = ", ".join(d.nombre_completo for d in docentes)
        return f"Docentes sin asignaturas: {nombres}."

    # Alumnos sin matrícula
    patrones_alumnos_sin_matricula = [
        "alumnos sin matrícula",
        "alumnos sin matricula",
        "alumnos no matriculados",
        "quiénes no están matriculados",
        "quienes no estan matriculados"
    ]
    if any(p in t for p in patrones_alumnos_sin_matricula):
        alumnos_con_matricula_ids = [row.alumno_id for row in db.execute(matriculas.select()).fetchall()]
        alumnos = db.query(Alumno).filter(~Alumno.id.in_(alumnos_con_matricula_ids) if alumnos_con_matricula_ids else Alumno.id != None).all()
        if not alumnos:
            return "Todos los alumnos tienen al menos una matrícula registrada."
        nombres = ", ".join(a.nombre_completo for a in alumnos)
        return f"Alumnos sin matrícula: {nombres}."

    # Docentes sin reportes
    patrones_docentes_sin_reportes = [
        "docentes sin reportes", "docentes sin reporte",
        "que docentes no enviaron reportes", "qué docentes no enviaron reportes",
        "docentes que no enviaron reportes"
    ]
    if any(p in t for p in patrones_docentes_sin_reportes) or ("docentes" in t and "sin reportes" in t):
        label = ""
        q = db.query(ReporteDocente)
        # Filtros opcionales
        if "hoy" in t:
            from datetime import datetime
            inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            q = q.filter(ReporteDocente.fecha_envio >= inicio)
            label = " (hoy)"
        elif "este mes" in t:
            from datetime import datetime
            inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            q = q.filter(ReporteDocente.fecha_envio >= inicio_mes)
            label = " (este mes)"
        # Asignatura
        asig_nombre = None
        for clave in ["de asignatura ", "en asignatura ", "asignatura "]:
            if clave in t:
                asig_nombre = t.split(clave, 1)[1].strip()
                break
        if asig_nombre:
            q = q.filter(ReporteDocente.asignatura.ilike(f"%{asig_nombre}%"))
            label += " - asignatura: " + asig_nombre
        # Tipo
        tipo_nombre = None
        for clave in ["tipo evaluacion ", "tipo evaluación ", "tipo de ", "tipo "]:
            if clave in t:
                tipo_nombre = t.split(clave, 1)[1].strip()
                break
        if tipo_nombre:
            q = q.filter(ReporteDocente.tipo_evaluacion.ilike(f"%{tipo_nombre}%"))
            label += " - tipo: " + tipo_nombre
        # Docentes sin reportes en el filtro
        con_ids = [row[0] for row in q.with_entities(ReporteDocente.docente_id).distinct().all() if row[0] is not None]
        docentes_sin = db.query(Docente).filter(~Docente.id.in_(con_ids) if con_ids else Docente.id != None).all()
        if not docentes_sin:
            return "Todos los docentes tienen al menos un reporte" + label + "."
        nombres = ", ".join(d.nombre_completo for d in docentes_sin)
        return "Docentes sin reportes" + label + ": " + nombres + "."

    # Resumen: reportes por asignatura
    patrones_reportes_por_asignatura = [
        "reportes por asignatura", "cantidad de reportes por asignatura",
        "total de reportes por asignatura", "resumen de reportes por asignatura"
    ]
    if any(p in t for p in patrones_reportes_por_asignatura):
        label = ""
        q = db.query(ReporteDocente)
        # Filtros de tiempo
        if "hoy" in t:
            from datetime import datetime
            inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            q = q.filter(ReporteDocente.fecha_envio >= inicio)
            label = " (hoy)"
        elif "este mes" in t:
            from datetime import datetime
            inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            q = q.filter(ReporteDocente.fecha_envio >= inicio_mes)
            label = " (este mes)"
        # Filtro por tipo
        tipo_nombre = None
        for clave in ["tipo evaluacion ", "tipo evaluación ", "tipo de ", "tipo "]:
            if clave in t:
                tipo_nombre = t.split(clave, 1)[1].strip()
                break
        if tipo_nombre:
            q = q.filter(ReporteDocente.tipo_evaluacion.ilike(f"%{tipo_nombre}%"))
            label += " - tipo: " + tipo_nombre
        rows = q.with_entities(ReporteDocente.asignatura, func.count(ReporteDocente.id)).group_by(ReporteDocente.asignatura).order_by(func.count(ReporteDocente.id).desc()).all()
        if not rows:
            return "No hay reportes" + label + "."
        partes = [f"{asig or 'Sin asignatura'} ({cnt})" for asig, cnt in rows]
        return "Reportes por asignatura" + label + ": " + ", ".join(partes) + "."

    # Listar reportes por fecha (más recientes primero)
    patrones_listar_reportes = [
        "listar reportes", "ver reportes", "reportes enviados", "reportes por fecha",
        "últimos reportes", "ultimos reportes", "reportes recientes"
    ]
    if any(p in t for p in patrones_listar_reportes) or ("reportes" in t and "por fecha" in t):
        label = ""
        q = db.query(ReporteDocente)
        # Filtros de tiempo
        if "hoy" in t:
            from datetime import datetime
            inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            q = q.filter(ReporteDocente.fecha_envio >= inicio)
            label = " (hoy)"
        elif "este mes" in t:
            from datetime import datetime
            inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            q = q.filter(ReporteDocente.fecha_envio >= inicio_mes)
            label = " (este mes)"
        # Filtros por asignatura y tipo
        asig_nombre = None
        for clave in ["de asignatura ", "en asignatura ", "asignatura "]:
            if clave in t:
                asig_nombre = t.split(clave, 1)[1].strip()
                break
        if asig_nombre:
            q = q.filter(ReporteDocente.asignatura.ilike(f"%{asig_nombre}%"))
            label += " - asignatura: " + asig_nombre
        tipo_nombre = None
        for clave in ["tipo evaluacion ", "tipo evaluación ", "tipo de ", "tipo "]:
            if clave in t:
                tipo_nombre = t.split(clave, 1)[1].strip()
                break
        if tipo_nombre:
            q = q.filter(ReporteDocente.tipo_evaluacion.ilike(f"%{tipo_nombre}%"))
            label += " - tipo: " + tipo_nombre
        # Ordenar por fecha y limitar
        q = q.order_by(ReporteDocente.fecha_envio.desc())
        reportes = q.limit(30).all()
        if not reportes:
            return "No hay reportes" + label + "."
        partes = []
        for rep in reportes:
            try:
                fecha_str = rep.fecha_envio.strftime("%Y-%m-%d %H:%M") if rep.fecha_envio else "sin fecha"
            except Exception:
                fecha_str = str(rep.fecha_envio) if rep.fecha_envio else "sin fecha"
            doc_nombre = rep.nombre_docente
            if not doc_nombre and rep.docente_id:
                d = db.query(Docente).filter(Docente.id == rep.docente_id).first()
                doc_nombre = d.nombre_completo if d else "Docente"
            partes.append(f"{fecha_str} - {doc_nombre or 'Docente'} - {rep.asignatura or 'Sin asignatura'} - {rep.tipo_evaluacion}")
        extra = q.count() - len(reportes)
        extra_str = f" (+{extra} más)" if extra > 0 else ""
        return "Reportes por fecha" + label + ": " + "; ".join(partes) + extra_str + "."

    # Alumnos matriculados por ciclo
    patrones_alumnos_por_ciclo = [
        "alumnos matriculados por ciclo", "cuantos alumnos por ciclo", "cuántos alumnos por ciclo",
        "alumnos por ciclo", "cantidad de alumnos por ciclo", "matriculados por ciclo",
        "cuantos alumnos hay por ciclo", "cuántos alumnos hay por ciclo",
        "distribucion de alumnos por ciclo", "distribución de alumnos por ciclo"
    ]
    if any(p in t for p in patrones_alumnos_por_ciclo):
        # Obtener IDs de alumnos matriculados
        matriculas_data = db.execute(matriculas.select()).fetchall()
        alumnos_matriculados_ids = list({r.alumno_id for r in matriculas_data})
        
        if not alumnos_matriculados_ids:
            return "No hay alumnos matriculados en el sistema."
        
        # Agrupar por ciclo
        rows = db.query(Alumno.ciclo, func.count(Alumno.id)).filter(
            Alumno.id.in_(alumnos_matriculados_ids)
        ).group_by(Alumno.ciclo).order_by(Alumno.ciclo).all()
        
        if not rows:
            return "No se encontraron ciclos para los alumnos matriculados."
        
        partes = [f"{ciclo or 'Sin ciclo'}: {cnt}" for ciclo, cnt in rows]
        total = sum(cnt for _, cnt in rows)
        return f"Alumnos matriculados por ciclo (Total: {total}): " + "; ".join(partes) + "."

    # Listar docentes (ordenados por nombre)
    patrones_listar_docentes = [
        "listar docentes", "ver docentes"
    ]
    if any(p in t for p in patrones_listar_docentes):
        q = db.query(Docente).order_by(Docente.nombre_completo.asc())
        docentes = q.limit(50).all()
        if not docentes:
            return "No hay docentes registrados."
        nombres = [d.nombre_completo or "Sin nombre" for d in docentes]
        extra = q.count() - len(docentes)
        extra_str = f" (+{extra} más)" if extra > 0 else ""
        return "Docentes: " + ", ".join(nombres) + extra_str + "."

    # Listar asignaturas (con docente y ciclo si están disponibles) con filtro por docente y límite configurable
    patrones_listar_asignaturas = [
        "listar asignaturas", "ver asignaturas"
    ]
    if any(p in t for p in patrones_listar_asignaturas):
        docente_nombre = None
        for clave in ["de docente ", "del docente ", "de "]:
            if clave in t:
                tmp = t.split(clave, 1)[1].strip()
                if tmp:
                    docente_nombre = tmp
                break
        label = ""
        if docente_nombre:
            d = db.query(Docente).filter(Docente.nombre_completo.ilike(f"%{docente_nombre}%")).first()
            if not d:
                return f"No encuentro un docente que coincida con '{docente_nombre}'."
            q = db.query(Asignatura).filter(Asignatura.docente_id == d.id).order_by(Asignatura.nombre.asc())
            label = f" (docente: {d.nombre_completo})"
        else:
            q = db.query(Asignatura).order_by(Asignatura.nombre.asc())
        # Límite configurable mediante número en el texto (máx 200)
        limite = 50
        for token in t.split():
            if token.isdigit():
                try:
                    val = int(token)
                    if val > 0:
                        limite = min(val, 200)
                        break
                except Exception:
                    pass
        asignaturas = q.limit(limite).all()
        if not asignaturas:
            return "No hay asignaturas registradas."
        partes = []
        for a in asignaturas:
            doc = db.query(Docente).filter(Docente.id == a.docente_id).first() if getattr(a, "docente_id", None) else None
            doc_nombre = doc.nombre_completo if doc else None
            ciclo = getattr(a, "ciclo", None)
            detalle = a.nombre or "Sin nombre"
            anexos = []
            if doc_nombre:
                anexos.append(doc_nombre)
            if ciclo:
                anexos.append(f"ciclo {ciclo}")
            if anexos:
                detalle += " (" + ", ".join(anexos) + ")"
            partes.append(detalle)
        extra = q.count() - len(asignaturas)
        extra_str = f" (+{extra} más)" if extra > 0 else ""
        return "Asignaturas" + label + ": " + "; ".join(partes) + extra_str + "."

    # Listar alumnos (y sus ciclos si se solicita) con filtro por ciclo y límite configurable
    patrones_listar_alumnos = [
        "listar alumnos", "ver alumnos"
    ]
    if any(p in t for p in patrones_listar_alumnos):
        q = db.query(Alumno).order_by(Alumno.nombre_completo.asc())
        # Filtro por ciclo si se indica "ciclo X"
        ciclo_val = None
        if "ciclo " in t:
            resto = t.split("ciclo ", 1)[1].strip()
            num = resto.split()[0] if resto else ""
            if num.isdigit():
                try:
                    ciclo_val = int(num)
                except Exception:
                    ciclo_val = None
        if ciclo_val is not None:
            q = q.filter(Alumno.ciclo == ciclo_val)
        # Límite configurable mediante número en el texto (máx 200)
        limite = 50
        for token in t.split():
            if token.isdigit():
                try:
                    val = int(token)
                    if val > 0:
                        limite = min(val, 200)
                        break
                except Exception:
                    pass
        alumnos = q.limit(limite).all()
        if not alumnos:
            return "No hay alumnos registrados."
        incluir_ciclos = ("ciclo" in t) or ("ciclos" in t) or ("sus ciclos" in t) or ("y sus ciclos" in t)
        extra = q.count() - len(alumnos)
        extra_str = f" (+{extra} más)" if extra > 0 else ""
        label = f" (ciclo {ciclo_val})" if ciclo_val is not None else ""
        if incluir_ciclos:
            partes = [f"{(a.nombre_completo or 'Sin nombre')} ({(a.ciclo or 'Sin ciclo')})" for a in alumnos]
            return "Alumnos y sus ciclos" + label + ": " + ", ".join(partes) + extra_str + "."
        else:
            nombres = [a.nombre_completo or "Sin nombre" for a in alumnos]
            return "Alumnos" + label + ": " + ", ".join(nombres) + extra_str + "."

    # Listar matrículas (enrolments) con filtros y límite configurable
    patrones_listar_matriculas = [
        "listar matriculas", "listar matrículas", "ver matriculas", "ver matrículas"
    ]
    if any(p in t for p in patrones_listar_matriculas):
        # Base query con joins a Alumno, Asignatura y Docente
        q = db.query(Alumno, Asignatura, Docente).\
            join(matriculas, matriculas.c.alumno_id == Alumno.id).\
            join(Asignatura, matriculas.c.asignatura_id == Asignatura.id).\
            outerjoin(Docente, Docente.id == Asignatura.docente_id)
        label = ""
        # Filtro por asignatura
        asig_nombre = None
        for clave in ["de asignatura ", "en asignatura ", "asignatura "]:
            if clave in t:
                asig_nombre = t.split(clave, 1)[1].strip()
                break
        if asig_nombre:
            q = q.filter(Asignatura.nombre.ilike(f"%{asig_nombre}%"))
            label += f" (asignatura: {asig_nombre})"
        # Filtro por alumno
        alumno_nombre = None
        for clave in ["de alumno ", "alumno "]:
            if clave in t:
                alumno_nombre = t.split(clave, 1)[1].strip()
                break
        if alumno_nombre:
            q = q.filter(Alumno.nombre_completo.ilike(f"%{alumno_nombre}%"))
            label += f" (alumno: {alumno_nombre})"
        # Filtro por docente
        docente_nombre = None
        for clave in ["de docente ", "docente "]:
            if clave in t:
                docente_nombre = t.split(clave, 1)[1].strip()
                break
        if docente_nombre:
            q = q.filter(Docente.nombre_completo.ilike(f"%{docente_nombre}%"))
            label += f" (docente: {docente_nombre})"
        # Filtro por ciclo del alumno: "ciclo X"
        ciclo_val = None
        if "ciclo " in t:
            resto = t.split("ciclo ", 1)[1].strip()
            num = resto.split()[0] if resto else ""
            if num.isdigit():
                try:
                    ciclo_val = int(num)
                except Exception:
                    ciclo_val = None
        if ciclo_val is not None:
            q = q.filter(Alumno.ciclo == ciclo_val)
            label += f" (ciclo {ciclo_val})"
        # Límite configurable mediante número en el texto (máx 200)
        limite = 50
        for token in t.split():
            if token.isdigit():
                try:
                    val = int(token)
                    if val > 0:
                        limite = min(val, 200)
                        break
                except Exception:
                    pass
        rows = q.order_by(Asignatura.nombre.asc(), Alumno.nombre_completo.asc()).limit(limite).all()
        if not rows:
            return "No hay matrículas registradas" + (label or "") + "."
        partes = []
        for al, asig, doc in rows:
            doc_nombre = doc.nombre_completo if doc else None
            ciclo = getattr(al, "ciclo", None)
            detalle = f"{al.nombre_completo or 'Alumno'}"
            if ciclo is not None:
                detalle += f" (ciclo {ciclo})"
            detalle += f" - {asig.nombre or 'Asignatura'}"
            if doc_nombre:
                detalle += f" - {doc_nombre}"
            partes.append(detalle)
        extra = q.count() - len(rows)
        extra_str = f" (+{extra} más)" if extra > 0 else ""
        return "Matrículas" + ((" " + label) if label else "") + ": " + "; ".join(partes) + extra_str + "."

    return None


# --- Integración de respuestas basadas en datos para DOCENTE ---

def _responder_intentos_docente(texto: str, db: Session, current_user) -> Optional[str]:
    t = _normalizar_texto_basico(texto)

    # Saludo exacto "hola" con conteo de asignaturas
    if t == "hola":
        nombre_usuario = getattr(current_user, "nombre", None) or getattr(current_user, "email", None) or "usuario"
        docente_tmp = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
        if docente_tmp:
            num_asigs = db.query(Asignatura).filter(Asignatura.docente_id == docente_tmp.id).count()
            return f"Hola {nombre_usuario}! (Docente) Dictas {num_asigs} asignaturas."
        return f"Hola {nombre_usuario}! (Docente)"

    docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
    if not docente:
        return "No se encontró el perfil de docente vinculado al usuario."

    # Mis asignaturas
    patrones_mis_asignaturas = [
        "mis asignaturas",
        "qué asignaturas tengo",
        "que asignaturas tengo",
        "asignaturas que dicto"
    ]
    if any(p in t for p in patrones_mis_asignaturas):
        asignaturas = db.query(Asignatura).filter(Asignatura.docente_id == docente.id).all()
        if not asignaturas:
            return "No tienes asignaturas asignadas."
        nombres = ", ".join(a.nombre for a in asignaturas)
        return f"Tus asignaturas: {nombres}."

    # Alumnos de asignatura {nombre}
    if "alumnos de" in t or "alumnos en" in t or "alumnos matriculados en" in t:
        nombre = None
        for clave in ["alumnos de asignatura ", "alumnos de ", "alumnos en ", "alumnos matriculados en "]:
            if clave in t:
                nombre = t.split(clave, 1)[1].strip()
                break
        if nombre:
            asignatura = db.query(Asignatura).filter(
                Asignatura.docente_id == docente.id,
                Asignatura.nombre.ilike(f"%{nombre}%")
            ).first()
            if not asignatura:
                return f"No encuentro una asignatura tuya que coincida con '{nombre}'."
            matriculas_data = db.execute(
                matriculas.select().where(matriculas.c.asignatura_id == asignatura.id)
            ).fetchall()
            alumnos = []
            for m in matriculas_data:
                alumno = db.query(Alumno).filter(Alumno.id == m.alumno_id).first()
                if alumno:
                    alumnos.append(alumno.nombre_completo)
            if not alumnos:
                return f"No hay alumnos matriculados en {asignatura.nombre}."
            return f"Alumnos en {asignatura.nombre}: {', '.join(alumnos)}."

    # Notas en asignatura {nombre}
    if "notas de" in t or "notas en" in t:
        nombre = None
        for clave in ["notas de asignatura ", "notas de ", "notas en "]:
            if clave in t:
                nombre = t.split(clave, 1)[1].strip()
                break
        if nombre:
            asignatura = db.query(Asignatura).filter(
                Asignatura.docente_id == docente.id,
                Asignatura.nombre.ilike(f"%{nombre}%")
            ).first()
            if not asignatura:
                return f"No encuentro una asignatura tuya que coincida con '{nombre}'."
            notas_publicadas = db.query(Nota).filter(Nota.asignatura_id == asignatura.id, Nota.publicada == True).all()
            notas_no_publicadas = db.query(Nota).filter(Nota.asignatura_id == asignatura.id, Nota.publicada == False).count()
            if not notas_publicadas and notas_no_publicadas == 0:
                return f"No hay notas registradas para {asignatura.nombre}."
            promedio = None
            if notas_publicadas:
                promedio = round(sum(n.calificacion for n in notas_publicadas) / len(notas_publicadas), 2)
            partes = []
            if notas_publicadas:
                partes.append(f"{len(notas_publicadas)} publicadas (promedio {promedio})")
            if notas_no_publicadas:
                partes.append(f"{notas_no_publicadas} sin publicar")
            return f"Notas en {asignatura.nombre}: " + ", ".join(partes) + "."

    # Matriculados por mis asignaturas
    patrones_matriculados_mis_asigs = [
        "matriculados por mis asignaturas", "alumnos por mis asignaturas",
        "alumnos por cada asignatura que dicto", "matriculados por asignatura",
        "cuantos alumnos en mis asignaturas", "cuántos alumnos en mis asignaturas"
    ]
    if any(p in t for p in patrones_matriculados_mis_asigs):
        mis_asignaturas = db.query(Asignatura).filter(Asignatura.docente_id == docente.id).all()
        if not mis_asignaturas:
            return "No tienes asignaturas asignadas."
        partes = []
        total = 0
        for a in mis_asignaturas:
            mats = db.execute(matriculas.select().where(matriculas.c.asignatura_id == a.id)).fetchall()
            cnt = len(mats)
            total += cnt
            partes.append(f"{a.nombre} ({cnt})")
        return "Matriculados por tus asignaturas: " + ", ".join(partes) + f". Total: {total}."

    # Pendientes de publicación (opcionalmente en una asignatura)
    if ("pendientes" in t and ("publicar" in t or "publicación" in t)) or "notas sin publicar" in t:
        nombre = None
        for clave in ["pendientes de publicación en asignatura ", "pendientes de publicación en ", "pendientes en asignatura ", "pendientes en "]:
            if clave in t:
                nombre = t.split(clave, 1)[1].strip()
                break
        if nombre:
            asignatura = db.query(Asignatura).filter(
                Asignatura.docente_id == docente.id,
                Asignatura.nombre.ilike(f"%{nombre}%")
            ).first()
            if not asignatura:
                return f"No encuentro una asignatura tuya que coincida con '{nombre}'."
            pendientes = db.query(Nota).filter(Nota.asignatura_id == asignatura.id, Nota.publicada == False).count()
            return f"Pendientes de publicación en {asignatura.nombre}: {pendientes}."
        else:
            mis_asignaturas = db.query(Asignatura).filter(Asignatura.docente_id == docente.id).all()
            if not mis_asignaturas:
                return "No tienes asignaturas asignadas."
            partes = []
            total = 0
            for a in mis_asignaturas:
                cnt = db.query(Nota).filter(Nota.asignatura_id == a.id, Nota.publicada == False).count()
                total += cnt
                partes.append(f"{a.nombre} ({cnt})")
            return "Pendientes de publicación: " + ", ".join(partes) + f". Total: {total}."

    # Alumnos en riesgo en asignatura {nombre} con umbral opcional
    if "alumnos en riesgo" in t or "en riesgo en" in t or "riesgo en" in t:
        nombre = None
        for clave in ["alumnos en riesgo en asignatura ", "alumnos en riesgo en ", "en riesgo en asignatura ", "en riesgo en ", "riesgo en "]:
            if clave in t:
                nombre = t.split(clave, 1)[1].strip()
                break
        if nombre:
            # Umbral opcional
            umbral = 11.0
            import re
            m = re.search(r"umbral\s*(\d+(?:\.\d+)?)", t)
            if m:
                try:
                    umbral = float(m.group(1))
                except Exception:
                    pass
            asignatura = db.query(Asignatura).filter(
                Asignatura.docente_id == docente.id,
                Asignatura.nombre.ilike(f"%{nombre}%")
            ).first()
            if not asignatura:
                return f"No encuentro una asignatura tuya que coincida con '{nombre}'."
            mats = db.execute(matriculas.select().where(matriculas.c.asignatura_id == asignatura.id)).fetchall()
            en_riesgo = []
            for mrec in mats:
                al = db.query(Alumno).filter(Alumno.id == mrec.alumno_id).first()
                if not al:
                    continue
                proms = calcular_promedios_alumno(db, al.id, asignatura.id)
                final = proms.get("promedio_final")
                if final is not None and final < umbral:
                    en_riesgo.append(f"{al.nombre_completo} ({final})")
            if not en_riesgo:
                return f"No hay alumnos en riesgo en {asignatura.nombre} con umbral {umbral}."
            # Limitar a 30 elementos para evitar respuestas muy largas
            listado = en_riesgo[:30]
            extra = len(en_riesgo) - len(listado)
            extra_str = f" (+{extra} más)" if extra > 0 else ""
            return f"Alumnos en riesgo en {asignatura.nombre} (umbral {umbral}): " + ", ".join(listado) + extra_str + "."

    return None


@router.post("/chat/admin")
async def chat_admin(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    texto = _extraer_ultimo_mensaje_usuario(req)
    respuesta_datos = _responder_intentos_admin(texto, db, current_user)
    if respuesta_datos:
        return {"reply": respuesta_datos}
    system_prompt = ROLE_SYSTEM_PROMPTS["admin"]
    reply = _chat_with_groq(system_prompt, req)
    return {"reply": reply}


@router.post("/chat/docente")
async def chat_docente(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("docente"))
):
    texto = _extraer_ultimo_mensaje_usuario(req)
    respuesta_datos = _responder_intentos_docente(texto, db, current_user)
    if respuesta_datos:
        return {"reply": respuesta_datos}
    system_prompt = ROLE_SYSTEM_PROMPTS["docente"]
    reply = _chat_with_groq(system_prompt, req)
    return {"reply": reply}


@router.post("/chat/alumno")
async def chat_alumno(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("alumno"))
):
    texto = _extraer_ultimo_mensaje_usuario(req)
    respuesta_datos = _responder_intentos_alumno(texto, db, current_user)
    if respuesta_datos:
        return {"reply": respuesta_datos}
    system_prompt = ROLE_SYSTEM_PROMPTS["alumno"]
    reply = _chat_with_groq(system_prompt, req)
    return {"reply": reply}


def _responder_intentos_alumno(texto: str, db: Session, current_user) -> Optional[str]:
    t = _normalizar_texto_basico(texto)

    # Obtener perfil de alumno
    alumno = db.query(Alumno).filter(Alumno.usuario_id == current_user.id).first()
    if not alumno:
        return "No se encontró el perfil de alumno vinculado al usuario."

    # Saludo exacto "hola" con conteo de matrículas
    if t == "hola":
        nombre_usuario = getattr(current_user, "nombre", None) or getattr(current_user, "email", None) or "usuario"
        mats = db.execute(matriculas.select().where(matriculas.c.alumno_id == alumno.id)).fetchall()
        return f"Hola {nombre_usuario}! (Alumno) Tienes {len(mats)} matrículas activas."

    # Últimas notas (N opcional)
    if ("ultimas" in t or "últimas" in t) and "nota" in t:
        import re
        m = re.search(r"(?:ultimas|últimas)\s*(\d+)\s*notas", t)
        n = 5
        if m:
            try:
                n = max(1, min(30, int(m.group(1))))
            except Exception:
                pass
        notas = (
            db.query(Nota)
            .filter(Nota.alumno_id == alumno.id, Nota.publicada == True)
            .order_by(Nota.fecha_registro.desc())
            .limit(n)
            .all()
        )
        if not notas:
            return "No tienes notas publicadas aún."
        partes = []
        for nota in notas:
            asig = db.query(Asignatura).filter(Asignatura.id == nota.asignatura_id).first()
            an = asig.nombre if asig else "Asignatura"
            partes.append(f"{an} - {nota.tipo_nota}: {nota.calificacion}")
        return f"Últimas {len(notas)} notas: " + "; ".join(partes) + "."

    # Mis docentes por asignatura
    patrones_mis_docentes = [
        "mis docentes", "docentes de mis cursos", "docentes de mis asignaturas"
    ]
    if any(p in t for p in patrones_mis_docentes):
        mats = db.execute(matriculas.select().where(matriculas.c.alumno_id == alumno.id)).fetchall()
        if not mats:
            return "No estás matriculado en ninguna asignatura."
        entries = []
        vistos = set()
        for mrec in mats:
            asig = db.query(Asignatura).filter(Asignatura.id == mrec.asignatura_id).first()
            if not asig:
                continue
            doc = db.query(Docente).filter(Docente.id == asig.docente_id).first()
            docente_nombre = doc.nombre_completo if doc else "Docente"
            clave = (asig.nombre, docente_nombre)
            if clave in vistos:
                continue
            vistos.add(clave)
            entries.append(f"{asig.nombre}: {docente_nombre}")
        if not entries:
            return "No encontré docentes para tus asignaturas."
        return "Docentes de tus asignaturas: " + "; ".join(entries) + "."

    # Qué necesito para aprobar [asignatura] [umbral X]
    if ("necesito para aprobar" in t) or ("debo sacar en final" in t) or ("debo sacar en el final" in t):
        nombre = None
        for clave in [
            "aprobar ", "aprobar en ", "aprobar la asignatura ", "aprobar asignatura ",
            "final en ", "final de "
        ]:
            if clave in t:
                nombre = t.split(clave, 1)[1].strip()
                break
        if nombre is None and "para aprobar " in t:
            nombre = t.split("para aprobar ", 1)[1].strip()

        import re
        umbral = 11.0
        m = re.search(r"umbral\s*(\d+(?:\.\d+)?)", t)
        if m:
            try:
                umbral = float(m.group(1))
            except Exception:
                pass

        if not nombre:
            return "Indica la asignatura: por ejemplo, 'qué necesito para aprobar Matemática umbral 11'."

        asignatura = db.query(Asignatura).filter(Asignatura.nombre.ilike(f"%{nombre}%")).first()
        if not asignatura:
            return f"No encuentro una asignatura que coincida con '{nombre}'."

        # Verificar matrícula en la asignatura
        mat = db.execute(
            matriculas.select().where(
                matriculas.c.alumno_id == alumno.id,
                matriculas.c.asignatura_id == asignatura.id
            )
        ).first()
        if not mat:
            return f"No estás matriculado en {asignatura.nombre}."

        proms = calcular_promedios_alumno(db, alumno.id, asignatura.id)
        componentes = ["actividades", "practicas", "parciales", "examen_final"]
        existentes = [proms.get(k) for k in componentes if proms.get(k) is not None]
        faltantes = [k for k in componentes if proms.get(k) is None]

        if len(faltantes) == 0:
            pf = proms.get("promedio_final")
            if pf is not None and pf >= umbral:
                return f"Ya alcanzaste el umbral {umbral} en {asignatura.nombre} (promedio final {pf})."
            elif pf is not None:
                return f"No hay evaluaciones pendientes en {asignatura.nombre}; tu promedio final es {pf} (< {umbral})."
            else:
                return f"Para {asignatura.nombre}, ya registraste todos los componentes; revisa con tu docente."

        requerido_total = 4 * umbral
        suma_actual = sum(existentes)
        k = len(faltantes)
        necesario_por_componente = round(max(0.0, requerido_total - suma_actual) / k, 2)
        if necesario_por_componente > 20.0:
            necesario_por_componente = 20.0

        if k == 1 and "examen_final" in faltantes:
            return f"Para aprobar {asignatura.nombre} con umbral {umbral}, necesitas al menos {necesario_por_componente} en el examen final."
        else:
            faltantes_str = ", ".join(faltantes).replace("practicas", "prácticas").replace("examen_final", "examen final")
            return f"Para aprobar {asignatura.nombre} con umbral {umbral}, necesitas un promedio de {necesario_por_componente} en cada componente pendiente: {faltantes_str}."

    # Mis asignaturas
    patrones_mis_asignaturas = [
        "mis asignaturas", "asignaturas matriculadas", "qué cursos tengo", "que cursos tengo", "ver asignaturas"
    ]
    if any(p in t for p in patrones_mis_asignaturas):
        mats = db.execute(matriculas.select().where(matriculas.c.alumno_id == alumno.id)).fetchall()
        if not mats:
            return "No estás matriculado en ninguna asignatura."
        nombres = []
        vistos = set()
        for mrec in mats:
            asig = db.query(Asignatura).filter(Asignatura.id == mrec.asignatura_id).first()
            if asig and asig.nombre not in vistos:
                vistos.add(asig.nombre)
                nombres.append(asig.nombre)
        if not nombres:
            return "No encontré asignaturas para tus matrículas."
        return "Tus asignaturas: " + ", ".join(nombres) + "."

    # Mis notas (limite 30)
    patrones_mis_notas = [
        "mis notas", "todas las notas", "ver mis notas", "ver notas"
    ]
    if any(p in t for p in patrones_mis_notas):
        notas = (
            db.query(Nota)
            .filter(Nota.alumno_id == alumno.id, Nota.publicada == True)
            .order_by(Nota.fecha_registro.desc())
            .limit(30)
            .all()
        )
        if not notas:
            return "No tienes notas publicadas aún."
        partes = []
        for nota in notas:
            asig = db.query(Asignatura).filter(Asignatura.id == nota.asignatura_id).first()
            an = asig.nombre if asig else "Asignatura"
            partes.append(f"{an} - {nota.tipo_nota}: {nota.calificacion}")
        return f"Tus notas ({len(notas)}): " + "; ".join(partes) + "."

    # Notas en [asignatura]
    if ("notas en" in t) or ("notas de" in t) or ("mis notas en" in t):
        nombre = None
        for clave in ["mis notas en ", "notas en ", "notas de "]:
            if clave in t:
                nombre = t.split(clave, 1)[1].strip()
                break
        if nombre:
            asignatura = db.query(Asignatura).filter(Asignatura.nombre.ilike(f"%{nombre}%")).first()
            if not asignatura:
                return f"No encuentro una asignatura que coincida con '{nombre}'."
            # Verificar matrícula
            mat = db.execute(
                matriculas.select().where(
                    matriculas.c.alumno_id == alumno.id,
                    matriculas.c.asignatura_id == asignatura.id
                )
            ).first()
            if not mat:
                return f"No estás matriculado en {asignatura.nombre}."
            notas = db.query(Nota).filter(
                Nota.alumno_id == alumno.id,
                Nota.asignatura_id == asignatura.id,
                Nota.publicada == True
            ).order_by(Nota.fecha_registro.desc()).limit(30).all()
            if not notas:
                return f"No tienes notas publicadas en {asignatura.nombre}."
            partes = [f"{n.tipo_nota}: {n.calificacion}" for n in notas]
            return f"Notas en {asignatura.nombre}: " + "; ".join(partes) + "."

    # Promedio general
    patrones_promedio_general = ["promedio general", "mi promedio general"]
    if any(p in t for p in patrones_promedio_general):
        notas = db.query(Nota).filter(Nota.alumno_id == alumno.id, Nota.publicada == True).all()
        if not notas:
            return "No tienes notas publicadas para calcular el promedio general."
        promedio = round(sum(n.calificacion for n in notas) / len(notas), 2)
        return f"Tu promedio general es {promedio}."

    # Promedio en [asignatura]
    if ("promedio en" in t) or ("promedio de" in t):
        nombre = None
        for clave in ["promedio en ", "promedio de "]:
            if clave in t:
                nombre = t.split(clave, 1)[1].strip()
                break
        if nombre:
            asignatura = db.query(Asignatura).filter(Asignatura.nombre.ilike(f"%{nombre}%")).first()
            if not asignatura:
                return f"No encuentro una asignatura que coincida con '{nombre}'."
            # Verificar matrícula
            mat = db.execute(
                matriculas.select().where(
                    matriculas.c.alumno_id == alumno.id,
                    matriculas.c.asignatura_id == asignatura.id
                )
            ).first()
            if not mat:
                return f"No estás matriculado en {asignatura.nombre}."
            proms = calcular_promedios_alumno(db, alumno.id, asignatura.id)
            pf = proms.get("promedio_final")
            if pf is not None:
                return f"Promedio final en {asignatura.nombre}: {pf}."
            else:
                disponibles = []
                for k in ["actividades", "practicas", "parciales", "examen_final"]:
                    v = proms.get(k)
                    if v is not None:
                        label = k.replace("practicas", "prácticas").replace("examen_final", "examen final")
                        disponibles.append(f"{label}: {v}")
                if disponibles:
                    return f"Aún no hay promedio final en {asignatura.nombre}. Componentes: " + "; ".join(disponibles) + "."
                return f"No hay suficientes datos publicados para calcular promedio en {asignatura.nombre}."

    # Promedios por asignatura
    patrones_promedios_por_asig = ["promedios por asignatura", "promedios de mis asignaturas"]
    if any(p in t for p in patrones_promedios_por_asig):
        mats = db.execute(matriculas.select().where(matriculas.c.alumno_id == alumno.id)).fetchall()
        if not mats:
            return "No estás matriculado en ninguna asignatura."
        partes = []
        vistos = set()
        for mrec in mats:
            asig = db.query(Asignatura).filter(Asignatura.id == mrec.asignatura_id).first()
            if not asig or asig.id in vistos:
                continue
            vistos.add(asig.id)
            proms = calcular_promedios_alumno(db, alumno.id, asig.id)
            pf = proms.get("promedio_final")
            if pf is not None:
                partes.append(f"{asig.nombre} ({pf})")
            else:
                partes.append(f"{asig.nombre} (sin promedio final)")
        if not partes:
            return "No hay promedios por asignatura disponibles."
        # Limitar para evitar mensajes largos
        listado = partes[:30]
        extra = len(partes) - len(listado)
        extra_str = f" (+{extra} más)" if extra > 0 else ""
        return "Promedios por asignatura: " + ", ".join(listado) + extra_str + "."

    # Ver promedios (general y por asignatura)
    patrones_ver_promedios = ["ver promedios", "mis promedios"]
    if any(p in t for p in patrones_ver_promedios):
        # Promedio general
        notas_pub = db.query(Nota).filter(Nota.alumno_id == alumno.id, Nota.publicada == True).all()
        if not notas_pub:
            return "No tienes notas publicadas para calcular promedios."
        promedio_general = round(sum(n.calificacion for n in notas_pub) / len(notas_pub), 2)
        # Promedios por asignatura (final si disponible)
        mats = db.execute(matriculas.select().where(matriculas.c.alumno_id == alumno.id)).fetchall()
        partes = []
        vistos = set()
        for mrec in mats:
            asig = db.query(Asignatura).filter(Asignatura.id == mrec.asignatura_id).first()
            if not asig or asig.id in vistos:
                continue
            vistos.add(asig.id)
            proms = calcular_promedios_alumno(db, alumno.id, asig.id)
            pf = proms.get("promedio_final")
            if pf is not None:
                partes.append(f"{asig.nombre} ({pf})")
            else:
                partes.append(f"{asig.nombre} (sin promedio final)")
        listado = partes[:20]
        extra = len(partes) - len(listado)
        extra_str = f" (+{extra} más)" if extra > 0 else ""
        return f"Tu promedio general es {promedio_general}. Promedios por asignatura: " + ", ".join(listado) + extra_str + "."

    # Ver historial académico del alumno
    patrones_ver_historial = ["ver historial", "mi historial", "ver historial academico", "ver historial académico"]
    if any(p in t for p in patrones_ver_historial):
        # Límite configurable mediante número en el texto (máx 50)
        limite = 10
        for token in t.split():
            if token.isdigit():
                try:
                    val = int(token)
                    if val > 0:
                        limite = min(val, 50)
                        break
                except Exception:
                    pass
        historiales = db.query(HistorialAcademico).filter(HistorialAcademico.alumno_id == alumno.id).order_by(HistorialAcademico.fecha_registro.desc()).limit(limite).all()
        if not historiales:
            return "No hay historial académico registrado a tu nombre."
        partes = []
        for h in historiales:
            try:
                fecha_str = h.fecha_registro.strftime("%Y-%m-%d") if h.fecha_registro else "sin fecha"
            except Exception:
                fecha_str = str(h.fecha_registro) if h.fecha_registro else "sin fecha"
            # Top 3 asignaturas con promedio
            asigns = db.query(AsignaturaHistorial).filter(AsignaturaHistorial.historial_id == h.id).all()
            top = asigns[:3]
            if top:
                det = ", ".join([f"{a.nombre} ({round(a.promedio,2)})" for a in top])
                extra_a = len(asigns) - len(top)
                extra_a_str = f" (+{extra_a} más)" if extra_a > 0 else ""
                partes.append(f"{fecha_str} - ciclo {h.ciclo}: {det}{extra_a_str}")
            else:
                partes.append(f"{fecha_str} - ciclo {h.ciclo}")
        # Indicar si hay más fuera del límite
        total = db.query(HistorialAcademico).filter(HistorialAcademico.alumno_id == alumno.id).count()
        extra_total = total - len(historiales)
        extra_total_str = f" (+{extra_total} más)" if extra_total > 0 else ""
        return "Historial académico: " + "; ".join(partes) + extra_total_str + "."

    # ¿Qué profesor enseña [asignatura]?
    patrones_profesor_asignatura = [
        "profesor de ", "docente de ", "quién enseña ", "quien enseña ", "qué profesor enseña ", "que profesor enseña "
    ]
    if any(clave in t for clave in patrones_profesor_asignatura):
        nombre = None
        for clave in patrones_profesor_asignatura:
            if clave in t:
                nombre = t.split(clave, 1)[1].strip()
                break
        if nombre:
            asignatura = db.query(Asignatura).filter(Asignatura.nombre.ilike(f"%{nombre}%")).first()
            if not asignatura:
                return f"No encuentro una asignatura que coincida con '{nombre}'."
            docente = db.query(Docente).filter(Docente.id == asignatura.docente_id).first()
            if not docente:
                return f"La asignatura {asignatura.nombre} no tiene docente asignado."
            # Verificar matrícula y responder de forma informativa
            mat = db.execute(
                matriculas.select().where(
                    matriculas.c.alumno_id == alumno.id,
                    matriculas.c.asignatura_id == asignatura.id
                )
            ).first()
            if mat:
                return f"El docente de {asignatura.nombre} es {docente.nombre_completo}."
            else:
                return f"El docente de {asignatura.nombre} es {docente.nombre_completo}. Nota: no estás matriculado en esta asignatura."

    return None


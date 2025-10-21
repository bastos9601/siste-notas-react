from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Optional
from auth import require_role
import os
from dotenv import load_dotenv

# Asegurar carga de variables de entorno desde backend/.env
load_dotenv()

try:
    from groq import Groq
except Exception:
    Groq = None

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
        # Registrar error para depuración y retornar HTTP 502 legible
        print(f"[Chatbot] Error al invocar Groq: {e}")
        raise HTTPException(status_code=502, detail=f"Error al consultar el proveedor de IA: {str(e)}")


@router.post("/chat/admin")
async def chat_admin(req: ChatRequest, current_user=Depends(require_role("admin"))):
    """Chat para panel de administrador."""
    system_prompt = ROLE_SYSTEM_PROMPTS["admin"]
    reply = _chat_with_groq(system_prompt, req)
    return {"reply": reply}


@router.post("/chat/docente")
async def chat_docente(req: ChatRequest, current_user=Depends(require_role("docente"))):
    """Chat para panel de docente."""
    system_prompt = ROLE_SYSTEM_PROMPTS["docente"]
    reply = _chat_with_groq(system_prompt, req)
    return {"reply": reply}


@router.post("/chat/alumno")
async def chat_alumno(req: ChatRequest, current_user=Depends(require_role("alumno"))):
    """Chat para panel de alumno."""
    system_prompt = ROLE_SYSTEM_PROMPTS["alumno"]
    reply = _chat_with_groq(system_prompt, req)
    return {"reply": reply}
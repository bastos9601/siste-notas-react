from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from core.database import get_db
from models import ConfiguracionSistema, Usuario
from schemas import ConfiguracionSistema as ConfigSchema, ConfiguracionSistemaBase
from core.auth import require_role
import os
import uuid

# Cloudinary
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()

router = APIRouter()

@router.get("/configuracion", response_model=ConfigSchema)
async def obtener_configuracion(db: Session = Depends(get_db)):
    """Devuelve la configuración del sistema (pública). Crea una por defecto si no existe."""
    config = db.query(ConfiguracionSistema).first()
    if not config:
        config = ConfiguracionSistema(nombre_sistema="Sistema de Gestión de Notas", logo_url=None, modo_oscuro=False)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.put("/admin/configuracion", response_model=ConfigSchema)
async def actualizar_configuracion(
    data: ConfiguracionSistemaBase,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Actualiza la configuración del sistema (solo admin). Crea si no existe."""
    config = db.query(ConfiguracionSistema).first()
    if not config:
        config = ConfiguracionSistema(
            nombre_sistema=data.nombre_sistema,
            logo_url=data.logo_url,
            modo_oscuro=bool(getattr(data, 'modo_oscuro', False))
        )
        db.add(config)
    else:
        config.nombre_sistema = data.nombre_sistema
        config.logo_url = data.logo_url
        # Actualizar modo_oscuro si existe en payload
        try:
            config.modo_oscuro = bool(getattr(data, 'modo_oscuro', config.modo_oscuro))
        except Exception:
            pass
    db.commit()
    db.refresh(config)
    return config

@router.post("/admin/configuracion/logo/cloudinary")
async def subir_logo_cloudinary(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Sube el logo a Cloudinary y devuelve la URL pública sin guardar en disco local."""
    # Validar credenciales
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    if not (cloud_name and api_key and api_secret):
        raise HTTPException(status_code=500, detail="Faltan credenciales de Cloudinary en el backend.")

    # Validar tipo de archivo
    allowed_content_types = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
    if archivo.content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail="Formato no soportado. Use PNG/JPEG/WEBP/GIF.")

    # Configurar Cloudinary
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )

    # Crear un public_id único
    public_id = f"logos/{uuid.uuid4().hex}"

    try:
        # Subir a Cloudinary sin guardar en disco
        result = cloudinary.uploader.upload(
            archivo.file,
            public_id=public_id,
            resource_type="image",
            overwrite=True
        )
        url = result.get("secure_url") or result.get("url")
        if not url:
            raise HTTPException(status_code=500, detail="No se obtuvo URL desde Cloudinary.")
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo a Cloudinary: {str(e)}")

@router.post("/admin/configuracion/logo")
async def subir_logo(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin")),
    request: Request = None
):
    """Sube un archivo de imagen de logo al servidor y devuelve su URL pública."""
    if not archivo.content_type or not archivo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen.")

    # Construir rutas de almacenamiento en backend/uploads/logos
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    uploads_dir = os.path.join(backend_dir, "uploads", "logos")
    os.makedirs(uploads_dir, exist_ok=True)

    # Generar nombre único
    _, ext = os.path.splitext(archivo.filename or "logo")
    ext = ext.lower() if ext else ".png"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(uploads_dir, unique_name)

    # Guardar archivo
    content = await archivo.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Construir URL absoluta
    base_url = str(request.base_url).rstrip("/") if request else ""
    url = f"{base_url}/uploads/logos/{unique_name}" if base_url else f"/uploads/logos/{unique_name}"

    return {"url": url}
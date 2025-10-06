from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Usuario, Alumno, Docente, Asignatura, Nota, matriculas
from schemas import (
    AlumnoCreate, AlumnoUpdate, Alumno as AlumnoSchema,
    DocenteCreate, Docente as DocenteSchema,
    AsignaturaCreate, Asignatura as AsignaturaSchema,
    MatriculaCreate, Matricula
)
from auth import require_role, get_password_hash, verify_password

router = APIRouter()

# ========== GESTIÓN DE ALUMNOS ==========

@router.post("/alumnos", response_model=AlumnoSchema)
async def crear_alumno(
    alumno_data: AlumnoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Crear nuevo alumno"""
    print(f"DEBUG: Datos recibidos: {alumno_data}")
    
    # Verificar si el DNI ya existe
    existing_alumno = db.query(Alumno).filter(Alumno.dni == alumno_data.dni).first()
    if existing_alumno:
        print(f"DEBUG: DNI ya existe: {alumno_data.dni}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El DNI ya está registrado"
        )
    
    # Verificar si el email ya existe
    existing_user = db.query(Usuario).filter(Usuario.email == alumno_data.email).first()
    if existing_user:
        print(f"DEBUG: Email ya existe: {alumno_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Crear usuario
    hashed_password = get_password_hash(alumno_data.password)
    db_user = Usuario(
        nombre=alumno_data.nombre_completo.split()[0],  # Primer nombre
        email=alumno_data.email,
        password_hash=hashed_password,
        rol="alumno"
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Crear alumno
    db_alumno = Alumno(
        nombre_completo=alumno_data.nombre_completo,
        dni=alumno_data.dni,
        ciclo=alumno_data.ciclo,
        usuario_id=db_user.id
    )
    
    db.add(db_alumno)
    db.commit()
    db.refresh(db_alumno)
    
    return db_alumno

@router.put("/alumnos/{alumno_id}", response_model=AlumnoSchema)
async def actualizar_alumno(
    alumno_id: int,
    alumno_data: AlumnoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Actualizar alumno existente"""
    print(f"DEBUG UPDATE: Actualizando alumno {alumno_id}")
    print(f"DEBUG UPDATE: Datos recibidos: {alumno_data}")
    
    # Buscar el alumno
    db_alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if not db_alumno:
        print(f"DEBUG UPDATE: Alumno {alumno_id} no encontrado")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    # Verificar si el DNI ya existe en otro alumno
    existing_alumno = db.query(Alumno).filter(
        Alumno.dni == alumno_data.dni,
        Alumno.id != alumno_id
    ).first()
    if existing_alumno:
        print(f"DEBUG UPDATE: DNI {alumno_data.dni} ya existe en otro alumno")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El DNI ya está registrado en otro alumno"
        )
    
    # Verificar si el email ya existe en otro usuario
    existing_user = db.query(Usuario).filter(
        Usuario.email == alumno_data.email,
        Usuario.id != db_alumno.usuario_id
    ).first()
    if existing_user:
        print(f"DEBUG UPDATE: Email {alumno_data.email} ya existe en otro usuario")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado en otro usuario"
        )
    
    # Actualizar datos del alumno
    db_alumno.nombre_completo = alumno_data.nombre_completo
    db_alumno.dni = alumno_data.dni
    db_alumno.ciclo = alumno_data.ciclo
    
    # Actualizar datos del usuario
    db_alumno.usuario.nombre = alumno_data.nombre_completo.split()[0]  # Primer nombre
    db_alumno.usuario.email = alumno_data.email
    
    # Actualizar contraseña solo si se proporciona
    if alumno_data.password is not None and alumno_data.password.strip() != "":
        db_alumno.usuario.password_hash = get_password_hash(alumno_data.password)
    
    db.commit()
    db.refresh(db_alumno)
    
    return db_alumno

@router.delete("/alumnos/{alumno_id}")
async def eliminar_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Eliminar alumno"""
    # Buscar el alumno
    db_alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if not db_alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    # Eliminar en cascada: primero las notas, luego las matrículas
    # Eliminar todas las notas del alumno
    db.query(Nota).filter(Nota.alumno_id == alumno_id).delete()
    
    # Eliminar todas las matrículas del alumno
    db.execute(
        matriculas.delete().where(matriculas.c.alumno_id == alumno_id)
    )
    
    # Eliminar el usuario asociado primero
    usuario_id = db_alumno.usuario_id
    db.delete(db_alumno)
    db.commit()
    
    # Eliminar el usuario
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if db_usuario:
        db.delete(db_usuario)
        db.commit()
    
    return {"message": "Alumno eliminado correctamente junto con sus notas y matrículas"}

@router.get("/alumnos", response_model=List[AlumnoSchema])
async def listar_alumnos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Listar todos los alumnos"""
    alumnos = db.query(Alumno).all()
    return alumnos

@router.get("/alumnos/{alumno_id}", response_model=AlumnoSchema)
async def obtener_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Obtener alumno por ID"""
    alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    return alumno

# ========== GESTIÓN DE DOCENTES ==========

@router.post("/docentes", response_model=DocenteSchema)
async def crear_docente(
    docente_data: DocenteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Crear nuevo docente"""
    # Verificar si el DNI ya existe
    existing_docente = db.query(Docente).filter(Docente.dni == docente_data.dni).first()
    if existing_docente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El DNI ya está registrado"
        )
    
    # Verificar si el email ya existe
    existing_user = db.query(Usuario).filter(Usuario.email == docente_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Crear usuario
    hashed_password = get_password_hash(docente_data.password)
    db_user = Usuario(
        nombre=docente_data.nombre_completo.split()[0],  # Primer nombre
        email=docente_data.email,
        password_hash=hashed_password,
        rol="docente"
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Crear docente
    db_docente = Docente(
        nombre_completo=docente_data.nombre_completo,
        dni=docente_data.dni,
        usuario_id=db_user.id
    )
    
    db.add(db_docente)
    db.commit()
    db.refresh(db_docente)
    
    return db_docente

@router.get("/docentes", response_model=List[DocenteSchema])
async def listar_docentes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Listar todos los docentes"""
    docentes = db.query(Docente).all()
    return docentes

@router.get("/docentes/{docente_id}", response_model=DocenteSchema)
async def obtener_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Obtener docente por ID"""
    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    return docente

@router.put("/docentes/{docente_id}", response_model=DocenteSchema)
async def actualizar_docente(
    docente_id: int,
    docente_data: DocenteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Actualizar docente"""
    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    # Verificar si el DNI ya existe en otro docente
    existing_docente = db.query(Docente).filter(
        Docente.dni == docente_data.dni,
        Docente.id != docente_id
    ).first()
    if existing_docente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El DNI ya está registrado en otro docente"
        )
    
    # Verificar si el email ya existe en otro usuario
    existing_user = db.query(Usuario).filter(
        Usuario.email == docente_data.email,
        Usuario.id != docente.usuario_id
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Actualizar usuario asociado
    usuario = db.query(Usuario).filter(Usuario.id == docente.usuario_id).first()
    if usuario:
        usuario.nombre = docente_data.nombre_completo.split()[0]
        usuario.email = docente_data.email
        if docente_data.password:
            usuario.password_hash = get_password_hash(docente_data.password)
    
    # Actualizar docente
    docente.nombre_completo = docente_data.nombre_completo
    docente.dni = docente_data.dni
    
    db.commit()
    db.refresh(docente)
    return docente

@router.delete("/docentes/{docente_id}")
async def eliminar_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Eliminar docente"""
    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    # Verificar si el docente tiene asignaturas asignadas
    asignaturas = db.query(Asignatura).filter(Asignatura.docente_id == docente_id).all()
    if asignaturas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el docente porque tiene asignaturas asignadas"
        )
    
    # Eliminar usuario asociado
    usuario = db.query(Usuario).filter(Usuario.id == docente.usuario_id).first()
    if usuario:
        db.delete(usuario)
    
    db.delete(docente)
    db.commit()
    return {"message": "Docente eliminado correctamente"}

# ========== GESTIÓN DE ASIGNATURAS ==========

@router.post("/asignaturas", response_model=AsignaturaSchema)
async def crear_asignatura(
    asignatura_data: AsignaturaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Crear nueva asignatura"""
    # Verificar que el docente existe
    docente = db.query(Docente).filter(Docente.id == asignatura_data.docente_id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    # Crear asignatura
    db_asignatura = Asignatura(
        nombre=asignatura_data.nombre,
        docente_id=asignatura_data.docente_id
    )
    
    db.add(db_asignatura)
    db.commit()
    db.refresh(db_asignatura)
    
    return db_asignatura

@router.get("/asignaturas", response_model=List[AsignaturaSchema])
async def listar_asignaturas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Listar todas las asignaturas"""
    asignaturas = db.query(Asignatura).all()
    return asignaturas

@router.get("/asignaturas/{asignatura_id}", response_model=AsignaturaSchema)
async def obtener_asignatura(
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Obtener asignatura por ID"""
    asignatura = db.query(Asignatura).filter(Asignatura.id == asignatura_id).first()
    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada"
        )
    return asignatura

@router.put("/asignaturas/{asignatura_id}", response_model=AsignaturaSchema)
async def actualizar_asignatura(
    asignatura_id: int,
    asignatura_data: AsignaturaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Actualizar asignatura existente"""
    db_asignatura = db.query(Asignatura).filter(Asignatura.id == asignatura_id).first()
    if not db_asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada"
        )
    
    # Verificar que el docente existe
    docente = db.query(Docente).filter(Docente.id == asignatura_data.docente_id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    # Actualizar asignatura
    db_asignatura.nombre = asignatura_data.nombre
    db_asignatura.docente_id = asignatura_data.docente_id
    
    db.commit()
    db.refresh(db_asignatura)
    
    return db_asignatura

@router.delete("/asignaturas/{asignatura_id}")
async def eliminar_asignatura(
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Eliminar asignatura"""
    # Buscar la asignatura
    db_asignatura = db.query(Asignatura).filter(Asignatura.id == asignatura_id).first()
    if not db_asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada"
        )
    
    # Verificar si la asignatura tiene notas registradas
    notas_count = db.query(Nota).filter(Nota.asignatura_id == asignatura_id).count()
    if notas_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar la asignatura porque tiene {notas_count} nota(s) registrada(s). Elimine las notas primero."
        )
    
    # Verificar si la asignatura tiene matrículas
    matriculas_count = db.execute(
        matriculas.select().where(matriculas.c.asignatura_id == asignatura_id)
    ).fetchall()
    if matriculas_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar la asignatura porque tiene {len(matriculas_count)} matrícula(s) activa(s). Elimine las matrículas primero."
        )
    
    # Eliminar la asignatura
    db.delete(db_asignatura)
    db.commit()
    
    return {"message": "Asignatura eliminada correctamente"}

# ========== GESTIÓN DE MATRÍCULAS ==========

@router.post("/matriculas", response_model=Matricula)
async def matricular_alumno(
    matricula_data: MatriculaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Matricular alumno en asignatura"""
    # Verificar que el alumno existe
    alumno = db.query(Alumno).filter(Alumno.id == matricula_data.alumno_id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    # Verificar que la asignatura existe
    asignatura = db.query(Asignatura).filter(Asignatura.id == matricula_data.asignatura_id).first()
    if not asignatura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignatura no encontrada"
        )
    
    # Verificar si ya está matriculado
    existing_matricula = db.execute(
        matriculas.select().where(
            matriculas.c.alumno_id == matricula_data.alumno_id,
            matriculas.c.asignatura_id == matricula_data.asignatura_id
        )
    ).first()
    
    if existing_matricula:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El alumno ya está matriculado en esta asignatura"
        )
    
    # Crear matrícula
    db.execute(
        matriculas.insert().values(
            alumno_id=matricula_data.alumno_id,
            asignatura_id=matricula_data.asignatura_id
        )
    )
    db.commit()
    
    return Matricula(
        alumno_id=matricula_data.alumno_id,
        asignatura_id=matricula_data.asignatura_id,
        alumno=alumno,
        asignatura=asignatura
    )

@router.get("/matriculas", response_model=List[Matricula])
async def listar_matriculas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Listar todas las matrículas"""
    matriculas_data = db.execute(matriculas.select()).fetchall()
    result = []
    
    for matricula in matriculas_data:
        alumno = db.query(Alumno).filter(Alumno.id == matricula.alumno_id).first()
        asignatura = db.query(Asignatura).filter(Asignatura.id == matricula.asignatura_id).first()
        result.append(Matricula(
            alumno_id=matricula.alumno_id,
            asignatura_id=matricula.asignatura_id,
            alumno=alumno,
            asignatura=asignatura
        ))
    
    return result

@router.delete("/matriculas/{alumno_id}/{asignatura_id}")
async def eliminar_matricula(
    alumno_id: int,
    asignatura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Eliminar matrícula de alumno"""
    # Verificar que la matrícula existe
    existing_matricula = db.execute(
        matriculas.select().where(
            matriculas.c.alumno_id == alumno_id,
            matriculas.c.asignatura_id == asignatura_id
        )
    ).first()
    
    if not existing_matricula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matrícula no encontrada"
        )
    
    # Eliminar matrícula
    db.execute(
        matriculas.delete().where(
            matriculas.c.alumno_id == alumno_id,
            matriculas.c.asignatura_id == asignatura_id
        )
    )
    db.commit()
    
    return {"message": "Matrícula eliminada correctamente"}

@router.get("/notas")
async def listar_todas_notas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Listar todas las notas del sistema (solo admin)"""
    notas = db.query(Nota).join(Alumno).join(Asignatura).all()
    
    notas_data = []
    for nota in notas:
        notas_data.append({
            "id": nota.id,
            "alumno_id": nota.alumno_id,
            "alumno_nombre": nota.alumno.nombre_completo,
            "alumno_dni": nota.alumno.dni,
            "asignatura_id": nota.asignatura_id,
            "asignatura_nombre": nota.asignatura.nombre,
            "docente_nombre": nota.asignatura.docente.nombre_completo,
            "calificacion": nota.calificacion,
            "fecha_registro": nota.fecha_registro
        })
    
    return notas_data

# ========== DASHBOARD ==========

@router.get("/dashboard")
async def dashboard_admin(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Dashboard del administrador con estadísticas"""
    total_alumnos = db.query(Alumno).count()
    total_docentes = db.query(Docente).count()
    total_asignaturas = db.query(Asignatura).count()
    total_notas = db.query(Nota).count()
    
    return {
        "total_alumnos": total_alumnos,
        "total_docentes": total_docentes,
        "total_asignaturas": total_asignaturas,
        "total_notas": total_notas
    }

@router.post("/alumnos/{alumno_id}/enviar-contrasena")
async def enviar_contrasena_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Enviar contraseña o enlace de restablecimiento al alumno"""
    # Buscar el alumno
    alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado"
        )
    
    # Obtener el usuario asociado
    usuario = db.query(Usuario).filter(Usuario.id == alumno.usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario asociado no encontrado"
        )
    
    # Generar nueva contraseña temporal
    import secrets
    import string
    
    # Generar contraseña temporal de 8 caracteres
    password_chars = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(password_chars) for _ in range(8))
    
    # Actualizar la contraseña en la base de datos
    usuario.password_hash = get_password_hash(temp_password)
    db.commit()
    
    # Intentar enviar email
    try:
        from email_config import send_password_email
        email_result = await send_password_email(
            email=usuario.email,
            nombre=alumno.nombre_completo,
            temp_password=temp_password
        )
        
        if email_result["success"]:
            return {
                "message": "Contraseña temporal generada y enviada por email",
                "alumno": {
                    "id": alumno.id,
                    "nombre_completo": alumno.nombre_completo,
                    "email": usuario.email
                },
                "email_sent": True,
                "email_message": email_result["message"]
            }
        else:
            # Si falla el email, retornar la contraseña para mostrar al admin
            return {
                "message": "Contraseña temporal generada, pero falló el envío por email",
                "alumno": {
                    "id": alumno.id,
                    "nombre_completo": alumno.nombre_completo,
                    "email": usuario.email,
                    "temp_password": temp_password
                },
                "email_sent": False,
                "email_error": email_result["message"],
                "instructions": "La contraseña se generó correctamente pero no se pudo enviar por email. Configura las credenciales de email en el archivo .env"
            }
    except Exception as e:
        # Si hay error en el servicio de email, retornar la contraseña
        return {
            "message": "Contraseña temporal generada, pero falló el envío por email",
            "alumno": {
                "id": alumno.id,
                "nombre_completo": alumno.nombre_completo,
                "email": usuario.email,
                "temp_password": temp_password
            },
            "email_sent": False,
            "email_error": f"Error en el servicio de email: {str(e)}",
            "instructions": "La contraseña se generó correctamente pero no se pudo enviar por email. Verifica la configuración de email."
        }

@router.post("/docentes/{docente_id}/enviar-contrasena")
async def enviar_contrasena_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Enviar contraseña o enlace de restablecimiento al docente"""
    # Buscar el docente
    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docente no encontrado"
        )
    
    # Obtener el usuario asociado
    usuario = db.query(Usuario).filter(Usuario.id == docente.usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario asociado no encontrado"
        )
    
    # Generar nueva contraseña temporal
    import secrets
    import string
    
    # Generar contraseña temporal de 8 caracteres
    password_chars = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(password_chars) for _ in range(8))
    
    # Actualizar la contraseña en la base de datos
    usuario.password_hash = get_password_hash(temp_password)
    db.commit()
    
    # Intentar enviar email
    try:
        from email_config import send_password_email
        email_result = await send_password_email(
            email=usuario.email,
            nombre=docente.nombre_completo,
            temp_password=temp_password
        )
        
        if email_result["success"]:
            return {
                "message": "Contraseña temporal generada y enviada por email",
                "docente": {
                    "id": docente.id,
                    "nombre_completo": docente.nombre_completo,
                    "email": usuario.email
                },
                "email_sent": True,
                "email_message": email_result["message"]
            }
        else:
            # Si falla el email, retornar la contraseña para mostrar al admin
            return {
                "message": "Contraseña temporal generada, pero falló el envío por email",
                "docente": {
                    "id": docente.id,
                    "nombre_completo": docente.nombre_completo,
                    "email": usuario.email,
                    "temp_password": temp_password
                },
                "email_sent": False,
                "email_error": email_result["message"],
                "instructions": "La contraseña se generó correctamente pero no se pudo enviar por email. Configura las credenciales de email en el archivo .env"
            }
    except Exception as e:
        # Si hay error en el servicio de email, retornar la contraseña
        return {
            "message": "Contraseña temporal generada, pero falló el envío por email",
            "docente": {
                "id": docente.id,
                "nombre_completo": docente.nombre_completo,
                "email": usuario.email,
                "temp_password": temp_password
            },
            "email_sent": False,
            "email_error": f"Error en el servicio de email: {str(e)}",
            "instructions": "La contraseña se generó correctamente pero no se pudo enviar por email. Verifica la configuración de email."
        }
@ r o u t e r . p u t ( " / m i - p e r f i l " )  
 a s y n c   d e f   a c t u a l i z a r _ m i _ p e r f i l _ a d m i n (  
         p e r f i l _ d a t a :   d i c t ,  
         d b :   S e s s i o n   =   D e p e n d s ( g e t _ d b ) ,  
         c u r r e n t _ u s e r :   U s u a r i o   =   D e p e n d s ( r e q u i r e _ r o l e ( " a d m i n " ) )  
 ) :  
         " " " A c t u a l i z a r   e l   p e r f i l   d e l   a d m i n   ( c o n t r a s e � � a ) " " "  
         #   V e r i f i c a r   q u e   s e   p r o p o r c i o n � �   l a   c o n t r a s e � � a   a c t u a l  
         p a s s w o r d _ a c t u a l   =   p e r f i l _ d a t a . g e t ( " p a s s w o r d _ a c t u a l " )  
         i f   n o t   p a s s w o r d _ a c t u a l :  
                 r a i s e   H T T P E x c e p t i o n (  
                         s t a t u s _ c o d e = s t a t u s . H T T P _ 4 0 0 _ B A D _ R E Q U E S T ,  
                         d e t a i l = " L a   c o n t r a s e � � a   a c t u a l   e s   r e q u e r i d a "  
                 )  
          
         #   V e r i f i c a r   l a   c o n t r a s e � � a   a c t u a l  
         i f   n o t   v e r i f y _ p a s s w o r d ( p a s s w o r d _ a c t u a l ,   c u r r e n t _ u s e r . p a s s w o r d _ h a s h ) :  
                 r a i s e   H T T P E x c e p t i o n (  
                         s t a t u s _ c o d e = s t a t u s . H T T P _ 4 0 0 _ B A D _ R E Q U E S T ,  
                         d e t a i l = " L a   c o n t r a s e � � a   a c t u a l   e s   i n c o r r e c t a "  
                 )  
          
         #   V e r i f i c a r   q u e   s e   p r o p o r c i o n � �   l a   n u e v a   c o n t r a s e � � a  
         n u e v a _ p a s s w o r d   =   p e r f i l _ d a t a . g e t ( " n u e v a _ p a s s w o r d " )  
         i f   n o t   n u e v a _ p a s s w o r d :  
                 r a i s e   H T T P E x c e p t i o n (  
                         s t a t u s _ c o d e = s t a t u s . H T T P _ 4 0 0 _ B A D _ R E Q U E S T ,  
                         d e t a i l = " L a   n u e v a   c o n t r a s e � � a   e s   r e q u e r i d a "  
                 )  
          
         #   V e r i f i c a r   q u e   l a   n u e v a   c o n t r a s e � � a   t i e n e   a l   m e n o s   6   c a r a c t e r e s  
         i f   l e n ( n u e v a _ p a s s w o r d )   <   6 :  
                 r a i s e   H T T P E x c e p t i o n (  
                         s t a t u s _ c o d e = s t a t u s . H T T P _ 4 0 0 _ B A D _ R E Q U E S T ,  
                         d e t a i l = " L a   n u e v a   c o n t r a s e � � a   d e b e   t e n e r   a l   m e n o s   6   c a r a c t e r e s "  
                 )  
          
         #   A c t u a l i z a r   l a   c o n t r a s e � � a  
         c u r r e n t _ u s e r . p a s s w o r d _ h a s h   =   g e t _ p a s s w o r d _ h a s h ( n u e v a _ p a s s w o r d )  
         d b . c o m m i t ( )  
         d b . r e f r e s h ( c u r r e n t _ u s e r )  
          
         r e t u r n   {  
                 " m e s s a g e " :   " C o n t r a s e � � a   a c t u a l i z a d a   e x i t o s a m e n t e " ,  
                 " a d m i n " :   {  
                         " i d " :   c u r r e n t _ u s e r . i d ,  
                         " e m a i l " :   c u r r e n t _ u s e r . e m a i l ,  
                         " r o l " :   c u r r e n t _ u s e r . r o l  
                 }  
         }  
 
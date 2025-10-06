from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False)  # admin, docente, alumno
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    alumno = relationship("Alumno", back_populates="usuario", uselist=False)
    docente = relationship("Docente", back_populates="usuario", uselist=False)

class Alumno(Base):
    __tablename__ = "alumnos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(200), nullable=False)
    dni = Column(String(20), unique=True, index=True, nullable=False)
    ciclo = Column(String(50), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="alumno")
    notas = relationship("Nota", back_populates="alumno")
    asignaturas_matriculadas = relationship("Asignatura", secondary="matriculas", overlaps="alumnos_matriculados")

class Docente(Base):
    __tablename__ = "docentes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(200), nullable=False)
    dni = Column(String(20), unique=True, index=True, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="docente")
    asignaturas = relationship("Asignatura", back_populates="docente")

class Asignatura(Base):
    __tablename__ = "asignaturas"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    ciclo = Column(String(50), nullable=False)
    docente_id = Column(Integer, ForeignKey("docentes.id"), nullable=False)
    
    # Relaciones
    docente = relationship("Docente", back_populates="asignaturas")
    notas = relationship("Nota", back_populates="asignatura")
    alumnos_matriculados = relationship("Alumno", secondary="matriculas", overlaps="asignaturas_matriculadas")

class Nota(Base):
    __tablename__ = "notas"
    
    id = Column(Integer, primary_key=True, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False)
    asignatura_id = Column(Integer, ForeignKey("asignaturas.id"), nullable=False)
    calificacion = Column(Float, nullable=False)  # 0-20
    tipo_nota = Column(String(50), nullable=False)  # examen_final, examen_parcial, practica, participacion, etc.
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    publicada = Column(Boolean, default=False, nullable=False)  # Si la nota está publicada para el alumno
    
    # Relaciones
    alumno = relationship("Alumno", back_populates="notas")
    asignatura = relationship("Asignatura", back_populates="notas")

# Tabla de relación muchos a muchos para matrículas
from sqlalchemy import Table

matriculas = Table(
    'matriculas',
    Base.metadata,
    Column('alumno_id', Integer, ForeignKey('alumnos.id'), primary_key=True),
    Column('asignatura_id', Integer, ForeignKey('asignaturas.id'), primary_key=True)
)

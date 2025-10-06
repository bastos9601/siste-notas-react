#!/usr/bin/env python3
"""
Script para migrar datos de SQLite a PostgreSQL
Ejecutar este script antes del primer despliegue en producción
"""

import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate_from_sqlite_to_postgres():
    """Migra datos de SQLite a PostgreSQL"""
    
    # Configuración de SQLite (desarrollo)
    sqlite_db = "sistema_notas.db"
    
    # Configuración de PostgreSQL (producción)
    postgres_url = os.getenv("DATABASE_URL")
    
    if not postgres_url or "sqlite" in postgres_url:
        print("❌ DATABASE_URL no está configurado para PostgreSQL")
        return
    
    try:
        # Conectar a SQLite
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Conectar a PostgreSQL
        postgres_conn = psycopg2.connect(postgres_url)
        postgres_cursor = postgres_conn.cursor()
        
        print("🔄 Iniciando migración de datos...")
        
        # Obtener todas las tablas de SQLite
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = sqlite_cursor.fetchall()
        
        for table_name in tables:
            table_name = table_name[0]
            if table_name == 'sqlite_sequence':
                continue
                
            print(f"📋 Migrando tabla: {table_name}")
            
            # Obtener estructura de la tabla
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = sqlite_cursor.fetchall()
            
            # Obtener datos de la tabla
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if rows:
                # Crear columnas para la consulta INSERT
                column_names = [col[1] for col in columns]
                placeholders = ', '.join(['%s'] * len(column_names))
                columns_str = ', '.join(column_names)
                
                # Insertar datos en PostgreSQL
                insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                try:
                    postgres_cursor.executemany(insert_query, rows)
                    print(f"✅ {len(rows)} registros migrados en {table_name}")
                except Exception as e:
                    print(f"⚠️  Error al migrar {table_name}: {e}")
                    # Continuar con la siguiente tabla
        
        # Confirmar cambios
        postgres_conn.commit()
        print("🎉 Migración completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        if 'postgres_conn' in locals():
            postgres_conn.rollback()
    
    finally:
        # Cerrar conexiones
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'postgres_conn' in locals():
            postgres_conn.close()

def create_initial_data():
    """Crear datos iniciales si no existen"""
    from database import SessionLocal, engine
    from models import Usuario, Asignatura, Alumno, Docente, Matricula, Nota
    from auth import get_password_hash
    
    # Crear tablas
    from database import Base
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Verificar si ya existen datos
        if db.query(Usuario).first():
            print("📊 Los datos iniciales ya existen")
            return
        
        print("🔧 Creando datos iniciales...")
        
        # Crear usuario administrador
        admin = Usuario(
            email="admin@sistema.com",
            nombre="Administrador",
            apellido="Sistema",
            password_hash=get_password_hash("admin123"),
            rol="admin",
            activo=True
        )
        db.add(admin)
        
        # Crear docente de ejemplo
        docente = Usuario(
            email="docente@sistema.com",
            nombre="Juan",
            apellido="Pérez",
            password_hash=get_password_hash("docente123"),
            rol="docente",
            activo=True
        )
        db.add(docente)
        
        # Crear alumno de ejemplo
        alumno = Usuario(
            email="alumno@sistema.com",
            nombre="María",
            apellido="García",
            password_hash=get_password_hash("alumno123"),
            rol="alumno",
            activo=True
        )
        db.add(alumno)
        
        db.commit()
        
        # Crear asignatura de ejemplo
        asignatura = Asignatura(
            nombre="Matemáticas",
            codigo="MAT001",
            creditos=4,
            docente_id=docente.id
        )
        db.add(asignatura)
        
        db.commit()
        
        print("✅ Datos iniciales creados:")
        print("   👤 Admin: admin@sistema.com / admin123")
        print("   👨‍🏫 Docente: docente@sistema.com / docente123")
        print("   👨‍🎓 Alumno: alumno@sistema.com / alumno123")
        
    except Exception as e:
        print(f"❌ Error al crear datos iniciales: {e}")
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        migrate_from_sqlite_to_postgres()
    else:
        create_initial_data()

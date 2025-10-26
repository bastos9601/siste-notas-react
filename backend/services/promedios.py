from sqlalchemy.orm import Session
from models import Nota
from typing import Dict, Optional


def calcular_promedios_alumno(db: Session, alumno_id: int, asignatura_id: int) -> Dict[str, Optional[float]]:
    """
    Calcula los promedios de un alumno para una asignatura específica desde las notas publicadas.
    
    Fórmula: promedio_final = (actividades + practicas + parciales + examen_final) / 4
    
    Returns:
        Dict con: actividades, practicas, parciales, examen_final, promedio_final
    """
    # Obtener todas las notas publicadas del alumno para la asignatura
    notas = db.query(Nota).filter(
        Nota.alumno_id == alumno_id,
        Nota.asignatura_id == asignatura_id,
        Nota.publicada == True
    ).all()
    
    # Agrupar notas por tipo
    tipos_notas = {
        'actividades': [],
        'practicas': [],
        'parciales': [],
        'examen_final': []
    }
    
    for nota in notas:
        tipo_raw = str(nota.tipo_nota or '').strip().lower()
        
        # Mapeo directo y por contenido
        if tipo_raw in ['exposicion', 'exposición', 'tarea', 'trabajo_grupal', 'trabajo grupal', 'quiz', 'laboratorio', 'proyecto']:
            tipos_notas['actividades'].append(nota.calificacion)
        elif tipo_raw in ['actividad', 'actividades']:
            tipos_notas['actividades'].append(nota.calificacion)
        elif 'participacion' in tipo_raw or 'participación' in tipo_raw:
            tipos_notas['actividades'].append(nota.calificacion)
        elif tipo_raw in ['practica', 'práctica', 'practicas', 'prácticas']:
            tipos_notas['practicas'].append(nota.calificacion)
        elif tipo_raw in ['parcial', 'parciales', 'examen_parcial', 'examen parcial']:
            tipos_notas['parciales'].append(nota.calificacion)
        elif tipo_raw in ['examen_final', 'examen final', 'final']:
            tipos_notas['examen_final'].append(nota.calificacion)
        else:
            # Fallback: buscar por palabras clave
            if any(keyword in tipo_raw for keyword in ['actividad', 'tarea', 'quiz', 'exposicion', 'exposición', 'trabajo', 'proyecto', 'laboratorio']):
                tipos_notas['actividades'].append(nota.calificacion)
            elif any(keyword in tipo_raw for keyword in ['practica', 'práctica']):
                tipos_notas['practicas'].append(nota.calificacion)
            elif any(keyword in tipo_raw for keyword in ['parcial']):
                tipos_notas['parciales'].append(nota.calificacion)
            elif any(keyword in tipo_raw for keyword in ['final', 'examen']):
                tipos_notas['examen_final'].append(nota.calificacion)
    
    # Calcular promedios por tipo
    def promedio_tipo(notas_tipo):
        return round(sum(notas_tipo) / len(notas_tipo), 2) if notas_tipo else None
    
    actividades = promedio_tipo(tipos_notas['actividades'])
    practicas = promedio_tipo(tipos_notas['practicas'])
    parciales = promedio_tipo(tipos_notas['parciales'])
    examen_final = promedio_tipo(tipos_notas['examen_final'])
    
    # Calcular promedio final: (actividades + practicas + parciales + examen_final) / 4
    componentes = [actividades, practicas, parciales, examen_final]
    componentes_validos = [c for c in componentes if c is not None]
    
    if len(componentes_validos) == 4:
        promedio_final = round(sum(componentes_validos) / 4, 2)
    else:
        # Si no están todos los componentes, no calcular promedio final
        promedio_final = None
    
    return {
        'actividades': actividades,
        'practicas': practicas,
        'parciales': parciales,
        'examen_final': examen_final,
        'promedio_final': promedio_final
    }


def calcular_promedios_asignatura(db: Session, asignatura_id: int) -> Dict[int, Dict[str, Optional[float]]]:
    """
    Calcula los promedios de todos los alumnos matriculados en una asignatura.
    
    Returns:
        Dict[alumno_id, promedios] donde promedios tiene las claves:
        actividades, practicas, parciales, examen_final, promedio_final
    """
    from models import matriculas
    
    # Obtener todos los alumnos matriculados en la asignatura
    alumnos_matriculados = db.execute(
        matriculas.select().where(matriculas.c.asignatura_id == asignatura_id)
    ).fetchall()
    
    resultado = {}
    for matricula in alumnos_matriculados:
        alumno_id = matricula.alumno_id
        resultado[alumno_id] = calcular_promedios_alumno(db, alumno_id, asignatura_id)
    
    return resultado
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Plus, Edit, Trash2, Search, BookOpen, ArrowLeft, Send, EyeOff, Calendar, Mail, ChevronDown, ChevronRight } from 'lucide-react';
import { docenteService } from '../../services/docenteService';

const DocenteNotas = () => {
  const { asignaturaId, alumnoId } = useParams();
  const navigate = useNavigate();
  const [asignaturas, setAsignaturas] = useState([]);
  const [alumnos, setAlumnos] = useState([]);
  const [notas, setNotas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAsignatura, setSelectedAsignatura] = useState(asignaturaId ? parseInt(asignaturaId) : '');
  const [selectedAlumno, setSelectedAlumno] = useState(alumnoId ? parseInt(alumnoId) : '');
  const [showModal, setShowModal] = useState(false);
  const [editingNota, setEditingNota] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedAlumnos, setExpandedAlumnos] = useState(new Set());
  const [formData, setFormData] = useState({
    alumno_id: '',
    asignatura_id: '',
    calificacion: '',
    tipo_evaluacion: 'examen_final'
  });

  useEffect(() => {
    loadAsignaturas();
  }, []);

  useEffect(() => {
    if (selectedAsignatura) {
      loadAlumnosYNotas(selectedAsignatura);
    }
  }, [selectedAsignatura]);

  const loadAsignaturas = async () => {
    try {
      const data = await docenteService.getMisAsignaturas();
      setAsignaturas(data);
    } catch (error) {
      console.error('Error al cargar asignaturas:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAlumnosYNotas = async (asignaturaId) => {
    try {
      const [alumnosData, notasData] = await Promise.all([
        docenteService.getAlumnosPorAsignatura(asignaturaId),
        docenteService.getNotasPorAsignatura(asignaturaId)
      ]);
      setAlumnos(alumnosData);
      setNotas(notasData);
    } catch (error) {
      console.error('Error al cargar datos:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingNota) {
        await docenteService.actualizarNota(editingNota.id, {
          calificacion: parseFloat(formData.calificacion),
          tipo_nota: formData.tipo_evaluacion
        });
      } else {
        await docenteService.registrarNota({
          alumno_id: parseInt(formData.alumno_id),
          asignatura_id: parseInt(formData.asignatura_id),
          calificacion: parseFloat(formData.calificacion),
          tipo_nota: formData.tipo_evaluacion
        });
      }
      
      // Recargar datos después de guardar
      if (selectedAsignatura) {
        await loadAlumnosYNotas(selectedAsignatura);
      }
      
      setShowModal(false);
      resetForm();
      
      // Mostrar mensaje de éxito
      alert(editingNota ? 'Nota actualizada correctamente' : 'Nota agregada correctamente');
    } catch (error) {
      console.error('Error al guardar nota:', error);
      alert('Error al guardar la nota. Verifica que los datos sean correctos.');
    }
  };

  const handleDelete = async (notaId) => {
    if (window.confirm('¿Estás seguro de eliminar esta nota?')) {
      try {
        await docenteService.eliminarNota(notaId);
        
        // Recargar datos después de eliminar
        if (selectedAsignatura) {
          await loadAlumnosYNotas(selectedAsignatura);
        }
        
        alert('Nota eliminada correctamente');
      } catch (error) {
        console.error('Error al eliminar nota:', error);
        alert('Error al eliminar la nota. Inténtalo de nuevo.');
      }
    }
  };

  const handlePublicar = async (notaId, alumnoNombre) => {
    if (window.confirm(`¿Publicar esta nota para que ${alumnoNombre} pueda verla?`)) {
      try {
        const response = await docenteService.publicarNota(notaId);
        
        // Recargar datos después de publicar
        if (selectedAsignatura) {
          await loadAlumnosYNotas(selectedAsignatura);
        }
        
        alert(`✅ Nota publicada exitosamente\n\nLa nota ya está disponible para que ${alumnoNombre} pueda verla en el sistema.`);
      } catch (error) {
        console.error('Error al publicar nota:', error);
        const errorMessage = error.response?.data?.detail || 'Error al publicar la nota. Inténtalo de nuevo.';
        alert(`❌ Error: ${errorMessage}`);
      }
    }
  };

  const handleDespublicar = async (notaId, alumnoNombre) => {
    if (window.confirm(`¿Despublicar esta nota para que ${alumnoNombre} no pueda verla?`)) {
      try {
        const response = await docenteService.despublicarNota(notaId);
        
        // Recargar datos después de despublicar
        if (selectedAsignatura) {
          await loadAlumnosYNotas(selectedAsignatura);
        }
        
        const successMessage = `
✅ ${response.message}

Alumno: ${response.nota.alumno.nombre}
Asignatura: ${response.nota.asignatura}

La nota ha sido despublicada exitosamente.
        `;
        alert(successMessage);
      } catch (error) {
        console.error('Error al despublicar nota:', error);
        const errorMessage = error.response?.data?.detail || 'Error al despublicar la nota. Inténtalo de nuevo.';
        alert(`❌ Error: ${errorMessage}`);
      }
    }
  };

  const handleEnviarTodasLasNotas = async (alumnoId, alumnoNombre) => {
    if (window.confirm(`¿Enviar notificación de notas publicadas a ${alumnoNombre} por email?`)) {
      try {
        const response = await docenteService.enviarTodasLasNotas(selectedAsignatura, alumnoId);
        
        if (response.email_sent) {
          const successMessage = `✅ Notificación enviada exitosamente

Se ha enviado un email a ${alumnoNombre} (${response.alumno.email}) notificándole que sus notas de ${response.asignatura.nombre} ya están disponibles en el sistema.`;
          alert(successMessage);
        } else {
          const errorMessage = `⚠️ ${response.message}

Alumno: ${response.alumno.nombre}
Email: ${response.alumno.email}
Asignatura: ${response.asignatura.nombre}

Error: ${response.email_error}

${response.instructions}`;
          alert(errorMessage);
        }
      } catch (error) {
        console.error('Error al enviar notificación:', error);
        const errorMessage = error.response?.data?.detail || 'Error al enviar la notificación. Inténtalo de nuevo.';
        alert(`❌ Error: ${errorMessage}`);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      alumno_id: '',
      asignatura_id: '',
      calificacion: '',
      tipo_evaluacion: 'examen_final'
    });
    setEditingNota(null);
  };

  const toggleAlumnoExpansion = (alumnoId) => {
    setExpandedAlumnos(prev => {
      const newSet = new Set(prev);
      if (newSet.has(alumnoId)) {
        newSet.delete(alumnoId);
      } else {
        newSet.add(alumnoId);
      }
      return newSet;
    });
  };

  const getNotasForAlumno = (alumnoId) => {
    return notas.filter(nota => nota.alumno_id === alumnoId);
  };

  const calcularPromedios = (notasAlumno) => {
    // Filtrar solo notas publicadas
    const notasPublicadas = notasAlumno.filter(nota => nota.publicada);
    
    // Clasificar notas por tipo
    const actividades = notasPublicadas.filter(nota => 
      ['participacion', 'tarea', 'quiz', 'exposicion', 'laboratorio', 'trabajo_grupal'].includes(nota.tipo_nota)
    );
    
    const practicas = notasPublicadas.filter(nota => 
      nota.tipo_nota === 'practica'
    );
    
    const parciales = notasPublicadas.filter(nota => 
      nota.tipo_nota === 'examen_parcial'
    );
    
    const examenFinal = notasPublicadas.find(nota => 
      nota.tipo_nota === 'examen_final'
    );
    
    const proyectos = notasPublicadas.filter(nota => 
      nota.tipo_nota === 'proyecto'
    );
    
    // Calcular promedios
    const promedioActividades = actividades.length > 0 
      ? actividades.reduce((sum, nota) => sum + nota.calificacion, 0) / actividades.length 
      : 0;
    
    const promedioPracticas = practicas.length > 0 
      ? practicas.reduce((sum, nota) => sum + nota.calificacion, 0) / practicas.length 
      : 0;
    
    const promedioParciales = parciales.length > 0 
      ? parciales.reduce((sum, nota) => sum + nota.calificacion, 0) / parciales.length 
      : 0;
    
    const notaExamenFinal = examenFinal ? examenFinal.calificacion : 0;
    
    const promedioProyectos = proyectos.length > 0 
      ? proyectos.reduce((sum, nota) => sum + nota.calificacion, 0) / proyectos.length 
      : 0;
    
    // Promedio final dinámico: si hay proyectos, dividir entre 5; si no, entre 4
    let sumaPromedios = promedioActividades + promedioPracticas + promedioParciales + notaExamenFinal;
    let divisor = 4;
    let formulaTexto = "(Actividades + Prácticas + Parciales + Examen Final) ÷ 4";
    
    if (proyectos.length > 0) {
      sumaPromedios += promedioProyectos;
      divisor = 5;
      formulaTexto = "(Actividades + Prácticas + Parciales + Examen Final + Proyectos) ÷ 5";
    }
    
    const promedioFinal = sumaPromedios / divisor;
    
    return {
      promedioActividades,
      promedioPracticas,
      promedioParciales,
      notaExamenFinal,
      promedioProyectos,
      promedioFinal,
      cantidadActividades: actividades.length,
      cantidadPracticas: practicas.length,
      cantidadParciales: parciales.length,
      tieneExamenFinal: !!examenFinal,
      cantidadProyectos: proyectos.length,
      formulaTexto
    };
  };

  const filteredAlumnos = alumnos.filter(alumno => {
    // Si hay un alumnoId específico, solo mostrar ese alumno
    if (selectedAlumno) {
      return alumno.id === selectedAlumno;
    }
    
    // Si no hay alumnoId específico, aplicar filtro de búsqueda normal
    return alumno.nombre_completo.toLowerCase().includes(searchTerm.toLowerCase()) ||
           alumno.dni.includes(searchTerm);
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {asignaturaId && (
            <button
              onClick={() => navigate('/docente/asignaturas')}
              className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
              <span>Volver a Asignaturas</span>
            </button>
          )}
          {selectedAlumno && (
            <button
              onClick={() => navigate(`/docente/notas/${asignaturaId}`)}
              className="flex items-center space-x-2 text-blue-600 hover:text-blue-900 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
              <span>Volver a Todos los Alumnos</span>
            </button>
          )}
        </div>
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-gray-900">Gestión de Notas</h1>
          {selectedAsignatura && (
            <button
              onClick={() => {
                setFormData({
                  ...formData,
                  asignatura_id: selectedAsignatura
                });
                setShowModal(true);
              }}
              className="btn-primary flex items-center"
            >
              <Plus className="h-4 w-4 mr-2" />
              Nueva Nota
            </button>
          )}
        </div>
      </div>

      {/* Selector de asignatura */}
      {!asignaturaId && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Seleccionar Asignatura</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {asignaturas.map((asignatura) => (
              <button
                key={asignatura.id}
                onClick={() => setSelectedAsignatura(asignatura.id)}
                className={`p-4 rounded-lg border-2 text-left transition-colors ${
                  selectedAsignatura === asignatura.id
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <BookOpen className="h-5 w-5 text-primary-600 mr-3" />
                    <span className="font-medium text-gray-900">{asignatura.nombre}</span>
                  </div>
                  <div className="flex items-center text-sm text-gray-500">
                    <Calendar className="h-4 w-4 mr-1" />
                    <span>Ciclo {asignatura.ciclo}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Lista de alumnos y notas */}
      {selectedAsignatura && (
        <>
          {/* Búsqueda - solo mostrar si no hay alumno específico */}
          {!selectedAlumno && (
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Buscar alumno por nombre o DNI..."
                className="input-field pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          )}

          {/* Tabla de alumnos y notas */}
          <div className="card">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                      
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Alumno
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      DNI
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ciclo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Notas Registradas
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredAlumnos.map((alumno) => {
                    const notasAlumno = getNotasForAlumno(alumno.id);
                    const isExpanded = expandedAlumnos.has(alumno.id);
                    
                    return (
                      <React.Fragment key={alumno.id}>
                        {/* Fila principal del alumno */}
                        <tr className="hover:bg-gray-50 border-b-2 border-gray-200">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <button
                              onClick={() => toggleAlumnoExpansion(alumno.id)}
                              className="text-gray-600 hover:text-gray-900 focus:outline-none"
                              title={isExpanded ? "Ocultar notas" : "Ver notas"}
                            >
                              {isExpanded ? (
                                <ChevronDown className="h-5 w-5" />
                              ) : (
                                <ChevronRight className="h-5 w-5" />
                              )}
                            </button>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                      {alumno.nombre_completo}
                                    </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                      {alumno.dni}
                                    </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                      {alumno.ciclo}
                                    </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {notasAlumno.length > 0 ? (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                {notasAlumno.length} {notasAlumno.length === 1 ? 'nota' : 'notas'}
                              </span>
                            ) : (
                              <span className="text-gray-400">Sin notas</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button
                              onClick={() => {
                                setFormData({
                                  alumno_id: alumno.id,
                                  asignatura_id: selectedAsignatura,
                                  calificacion: '',
                                  tipo_evaluacion: 'examen_final'
                                });
                                setShowModal(true);
                              }}
                              className="text-green-600 hover:text-green-900"
                              title="Agregar nota"
                            >
                              <Plus className="h-5 w-5" />
                            </button>
                          </td>
                        </tr>
                        
                        {/* Filas de notas (solo se muestran si está expandido) */}
                        {isExpanded && notasAlumno.length > 0 && (
                          <>
                            <tr className="bg-gray-100">
                              <td></td>
                              <td className="px-6 py-2 text-xs font-semibold text-gray-700" colSpan="1">
                                NOTA
                              </td>
                              <td className="px-6 py-2 text-xs font-semibold text-gray-700">
                                TIPO DE EVALUACIÓN
                              </td>
                              <td className="px-6 py-2 text-xs font-semibold text-gray-700">
                                FECHA
                              </td>
                              <td className="px-6 py-2 text-xs font-semibold text-gray-700">
                                ESTADO
                              </td>
                              <td className="px-6 py-2 text-xs font-semibold text-gray-700">
                                ACCIONES
                              </td>
                            </tr>
                            {notasAlumno.map((nota) => (
                              <tr key={`nota-${nota.id}`} className="bg-gray-50 hover:bg-gray-100">
                                <td></td>
                                <td className="px-6 py-3 whitespace-nowrap text-sm">
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                    nota.calificacion >= 13 ? 'bg-green-100 text-green-800' :
                                    nota.calificacion >= 10 ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-red-100 text-red-800'
                                  }`}>
                                    {nota.calificacion}
                                  </span>
                                </td>
                                <td className="px-6 py-3 whitespace-nowrap text-sm">
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                    nota.tipo_nota === 'examen_final' ? 'bg-red-100 text-red-800' :
                                    nota.tipo_nota === 'examen_parcial' ? 'bg-orange-100 text-orange-800' :
                                    nota.tipo_nota === 'practica' ? 'bg-blue-100 text-blue-800' :
                                    nota.tipo_nota === 'participacion' ? 'bg-green-100 text-green-800' :
                                    nota.tipo_nota === 'trabajo_grupal' ? 'bg-purple-100 text-purple-800' :
                                    nota.tipo_nota === 'proyecto' ? 'bg-indigo-100 text-indigo-800' :
                                    nota.tipo_nota === 'laboratorio' ? 'bg-cyan-100 text-cyan-800' :
                                    nota.tipo_nota === 'tarea' ? 'bg-yellow-100 text-yellow-800' :
                                    nota.tipo_nota === 'quiz' ? 'bg-pink-100 text-pink-800' :
                                    'bg-gray-100 text-gray-800'
                                  }`}>
                                    {nota.tipo_nota === 'examen_final' ? 'Examen Final' :
                                     nota.tipo_nota === 'examen_parcial' ? 'Examen Parcial' :
                                     nota.tipo_nota === 'practica' ? 'Práctica' :
                                     nota.tipo_nota === 'participacion' ? 'Participación' :
                                     nota.tipo_nota === 'trabajo_grupal' ? 'Trabajo Grupal' :
                                     nota.tipo_nota === 'proyecto' ? 'Proyecto' :
                                     nota.tipo_nota === 'laboratorio' ? 'Laboratorio' :
                                     nota.tipo_nota === 'tarea' ? 'Tarea' :
                                     nota.tipo_nota === 'quiz' ? 'Quiz' :
                                     nota.tipo_nota === 'exposicion' ? 'Exposición' :
                                     nota.tipo_nota || 'Examen Final'}
                                  </span>
                                </td>
                                <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-500">
                                  {new Date(nota.fecha_registro).toLocaleDateString()}
                                </td>
                                <td className="px-6 py-3 whitespace-nowrap text-sm">
                                  {nota.publicada ? (
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                      Publicada
                                    </span>
                                  ) : (
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                      Borrador
                                    </span>
                                  )}
                                </td>
                                <td className="px-6 py-3 whitespace-nowrap text-sm font-medium">
                                  <div className="flex space-x-2">
                                    <button
                                      onClick={() => {
                                        setEditingNota(nota);
                                        setFormData({
                                          alumno_id: nota.alumno_id,
                                          asignatura_id: nota.asignatura_id,
                                          calificacion: nota.calificacion.toString(),
                                          tipo_evaluacion: nota.tipo_nota || 'examen_final'
                                        });
                                        setShowModal(true);
                                      }}
                                      className="text-primary-600 hover:text-primary-900"
                                      title="Editar nota"
                                    >
                                      <Edit className="h-4 w-4" />
                                    </button>
                                    {!nota.publicada && (
                                      <button
                                        onClick={() => handlePublicar(nota.id, alumno.nombre_completo)}
                                        className="text-green-600 hover:text-green-900"
                                        title="Publicar nota"
                                      >
                                        <Send className="h-4 w-4" />
                                      </button>
                                    )}
                                    {nota.publicada && (
                                      <button
                                        onClick={() => handleDespublicar(nota.id, alumno.nombre_completo)}
                                        className="text-orange-600 hover:text-orange-900"
                                        title="Despublicar nota"
                                      >
                                        <EyeOff className="h-4 w-4" />
                                      </button>
                                    )}
                                    <button
                                      onClick={() => handleDelete(nota.id)}
                                      className="text-red-600 hover:text-red-900"
                                      title="Eliminar nota"
                                    >
                                      <Trash2 className="h-4 w-4" />
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                            
                            {/* Fila de resumen de promedios */}
                            {(() => {
                              const promedios = calcularPromedios(notasAlumno);
                              return (
                                <>
                                  <tr className="bg-gradient-to-r from-purple-50 to-indigo-50 border-t-2 border-purple-200">
                                    <td></td>
                                    <td className="px-6 py-4" colSpan="5">
                                      <div className="space-y-3">
                                        <h4 className="text-sm font-bold text-gray-800 mb-3 flex items-center">
                                          📊 Resumen de Promedios
                                        </h4>
                                        
                                        <div className="grid grid-cols-2 gap-3">
                                          {/* Promedio de Actividades */}
                                          <div className="bg-white rounded-lg p-3 shadow-sm border border-purple-100">
                                            <div className="text-xs text-gray-600 mb-1">
                                              📝 Actividades ({promedios.cantidadActividades})
                                            </div>
                                            <div className="text-lg font-bold text-purple-600">
                                              {promedios.promedioActividades > 0 ? promedios.promedioActividades.toFixed(2) : '-'}
                                            </div>
                                          </div>
                                          
                                          {/* Promedio de Prácticas */}
                                          <div className="bg-white rounded-lg p-3 shadow-sm border border-blue-100">
                                            <div className="text-xs text-gray-600 mb-1">
                                              🔬 Prácticas ({promedios.cantidadPracticas})
                                            </div>
                                            <div className="text-lg font-bold text-blue-600">
                                              {promedios.promedioPracticas > 0 ? promedios.promedioPracticas.toFixed(2) : '-'}
                                            </div>
                                          </div>
                                          
                                          {/* Promedio de Parciales */}
                                          <div className="bg-white rounded-lg p-3 shadow-sm border border-orange-100">
                                            <div className="text-xs text-gray-600 mb-1">
                                              📋 Parciales ({promedios.cantidadParciales})
                                            </div>
                                            <div className="text-lg font-bold text-orange-600">
                                              {promedios.promedioParciales > 0 ? promedios.promedioParciales.toFixed(2) : '-'}
                                            </div>
                                          </div>
                                          
                                          {/* Examen Final */}
                                          <div className="bg-white rounded-lg p-3 shadow-sm border border-red-100">
                                            <div className="text-xs text-gray-600 mb-1">
                                              📝 Examen Final
                                            </div>
                                            <div className="text-lg font-bold text-red-600">
                                              {promedios.tieneExamenFinal ? promedios.notaExamenFinal.toFixed(2) : '-'}
                                            </div>
                                          </div>
                                          
                                          {/* Promedio de Proyectos */}
                                          {promedios.cantidadProyectos > 0 && (
                                            <div className="bg-white rounded-lg p-3 shadow-sm border border-indigo-100">
                                              <div className="text-xs text-gray-600 mb-1">
                                                🎯 Proyectos ({promedios.cantidadProyectos})
                                              </div>
                                              <div className="text-lg font-bold text-indigo-600">
                                                {promedios.promedioProyectos.toFixed(2)}
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                        
                                        {/* Promedio Final */}
                                        <div className="bg-gradient-to-r from-green-100 to-emerald-100 rounded-lg p-4 shadow-md border-2 border-green-300 mt-3">
                                          <div className="flex items-center justify-between">
                                            <div>
                                              <div className="text-sm font-semibold text-gray-700 mb-1">
                                                🏆 PROMEDIO FINAL
                                              </div>
                                              <div className="text-xs text-gray-600">
                                                {promedios.formulaTexto}
                                              </div>
                                            </div>
                                            <div className={`text-3xl font-bold ${
                                              promedios.promedioFinal >= 13 ? 'text-green-700' :
                                              promedios.promedioFinal >= 10 ? 'text-yellow-700' :
                                              'text-red-700'
                                            }`}>
                                              {promedios.promedioFinal > 0 ? promedios.promedioFinal.toFixed(2) : '-'}
                                            </div>
                                          </div>
                                          {promedios.promedioFinal > 0 && (
                                            <div className={`mt-2 text-xs font-semibold ${
                                              promedios.promedioFinal >= 13 ? 'text-green-700' :
                                              promedios.promedioFinal >= 10 ? 'text-yellow-700' :
                                              'text-red-700'
                                            }`}>
                                              Estado: {promedios.promedioFinal >= 13 ? '✅ Aprobado' :
                                                      promedios.promedioFinal >= 10 ? '⚠️ Recuperación' :
                                                      '❌ Desaprobado'}
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    </td>
                                  </tr>
                                </>
                              );
                            })()}
                            
                            {/* Fila de notificación */}
                            <tr className="bg-blue-50 hover:bg-blue-100">
                              <td></td>
                              <td className="px-6 py-3 text-sm font-medium text-blue-800" colSpan="4">
                                📧 Notificar al alumno que las notas están publicadas
                              </td>
                              <td className="px-6 py-3 text-sm font-medium">
                                <button
                                  onClick={() => handleEnviarTodasLasNotas(alumno.id, alumno.nombre_completo)}
                                  className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-md text-xs font-medium transition-colors"
                                  title="Enviar notificación de notas publicadas"
                                >
                                  <Mail className="h-3 w-3" />
                                  <span>Enviar Notificación</span>
                                </button>
                              </td>
                            </tr>
                          </>
                        )}
                        
                        {/* Mensaje si no hay notas y está expandido */}
                        {isExpanded && notasAlumno.length === 0 && (
                          <tr className="bg-gray-50">
                            <td></td>
                            <td className="px-6 py-4 text-sm text-gray-500 text-center" colSpan="5">
                              Este alumno no tiene notas registradas. Haz clic en el botón + para agregar una nota.
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Modal para crear/editar nota */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {editingNota ? 'Editar Nota' : 'Nueva Nota'}
              </h3>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                {!editingNota && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Alumno
                    </label>
                    <select
                      required
                      className="input-field"
                      value={formData.alumno_id}
                      onChange={(e) => setFormData({...formData, alumno_id: e.target.value})}
                    >
                      <option value="">Seleccionar alumno</option>
                      {alumnos.map((alumno) => (
                        <option key={alumno.id} value={alumno.id}>
                          {alumno.nombre_completo} - {alumno.dni}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Calificación (0-20)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="20"
                    step="0.1"
                    required
                    className="input-field"
                    value={formData.calificacion}
                    onChange={(e) => setFormData({...formData, calificacion: e.target.value})}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Tipo de Evaluación
                  </label>
                  <select
                    required
                    className="input-field"
                    value={formData.tipo_evaluacion}
                    onChange={(e) => setFormData({...formData, tipo_evaluacion: e.target.value})}
                  >
                    <option value="examen_final">Examen Final</option>
                    <option value="examen_parcial">Examen Parcial</option>
                    <option value="practica">Práctica</option>
                    <option value="participacion">Participación</option>
                    <option value="trabajo_grupal">Trabajo Grupal</option>
                    <option value="proyecto">Proyecto</option>
                    <option value="laboratorio">Laboratorio</option>
                    <option value="tarea">Tarea</option>
                    <option value="quiz">Quiz</option>
                    <option value="exposicion">Exposición</option>
                  </select>
                </div>
                
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      resetForm();
                    }}
                    className="btn-secondary"
                  >
                    Cancelar
                  </button>
                  <button type="submit" className="btn-primary">
                    {editingNota ? 'Actualizar' : 'Guardar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocenteNotas;

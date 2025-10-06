import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Plus, Edit, Trash2, Search, BookOpen, ArrowLeft, Send, EyeOff, Calendar } from 'lucide-react';
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
        
        if (response.email_sent) {
          // Email enviado exitosamente
          const successMessage = `
✅ ${response.message}

Alumno: ${response.nota.alumno.nombre}
Email: ${response.nota.alumno.email}
Asignatura: ${response.nota.asignatura}

La notificación por email ha sido enviada exitosamente.
          `;
          alert(successMessage);
        } else {
          // Email falló, pero la nota se publicó
          const fallbackMessage = `
⚠️ ${response.message}

Alumno: ${response.nota.alumno.nombre}
Email: ${response.nota.alumno.email}
Asignatura: ${response.nota.asignatura}

Error del email: ${response.email_error}

${response.instructions}
          `;
          alert(fallbackMessage);
        }
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

  const resetForm = () => {
    setFormData({
      alumno_id: '',
      asignatura_id: '',
      calificacion: '',
      tipo_evaluacion: 'examen_final'
    });
    setEditingNota(null);
  };

  const getNotasForAlumno = (alumnoId) => {
    return notas.filter(nota => nota.alumno_id === alumnoId);
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
                      Nota
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo de Evaluación
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fecha
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredAlumnos.map((alumno) => {
                    const notasAlumno = getNotasForAlumno(alumno.id);
                    return (
                      <React.Fragment key={alumno.id}>
                        {notasAlumno.length > 0 ? (
                          notasAlumno.map((nota, index) => (
                            <tr key={`${alumno.id}-${nota.id}`} className="hover:bg-gray-50">
                              {index === 0 && (
                                <>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900" rowSpan={notasAlumno.length}>
                                    {alumno.nombre_completo}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" rowSpan={notasAlumno.length}>
                                    {alumno.dni}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" rowSpan={notasAlumno.length}>
                                    {alumno.ciclo}
                                  </td>
                                </>
                              )}
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  nota.calificacion >= 13 ? 'bg-green-100 text-green-800' :
                                  nota.calificacion >= 10 ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-red-100 text-red-800'
                                }`}>
                                  {nota.calificacion}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
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
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {new Date(nota.fecha_registro).toLocaleDateString()}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
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
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
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
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr className="hover:bg-gray-50">
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
                              <span className="text-gray-400">Sin nota</span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              <span className="text-gray-400">-</span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              <span className="text-gray-400">-</span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <div className="flex space-x-2">
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
                                >
                                  <Plus className="h-4 w-4" />
                                </button>
                              </div>
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

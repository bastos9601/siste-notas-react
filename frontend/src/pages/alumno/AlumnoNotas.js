import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FileText, TrendingUp, Award, BookOpen, Search, ArrowLeft } from 'lucide-react';
import { alumnoService } from '../../services/alumnoService';

const AlumnoNotas = () => {
  const { asignaturaId } = useParams();
  const navigate = useNavigate();
  const [notas, setNotas] = useState([]);
  const [asignaturas, setAsignaturas] = useState([]);
  const [promedioGeneral, setPromedioGeneral] = useState(null);
  const [promediosPorAsignatura, setPromediosPorAsignatura] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAsignatura, setSelectedAsignatura] = useState(asignaturaId || '');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [notasData, asignaturasData, promedioData, promediosAsignaturaData] = await Promise.all([
        alumnoService.getMisNotas(),
        alumnoService.getMisAsignaturas(),
        alumnoService.getMiPromedio(),
        alumnoService.getPromedioPorAsignatura()
      ]);
      
      setNotas(notasData);
      setAsignaturas(asignaturasData);
      setPromedioGeneral(promedioData);
      setPromediosPorAsignatura(promediosAsignaturaData);
    } catch (error) {
      console.error('Error al cargar datos:', error);
    } finally {
      setLoading(false);
    }
  };

  const getNotasFiltradas = () => {
    let notasFiltradas = notas;

    if (selectedAsignatura) {
      notasFiltradas = notasFiltradas.filter(nota => nota.asignatura_id === parseInt(selectedAsignatura));
    }

    if (searchTerm) {
      notasFiltradas = notasFiltradas.filter(nota =>
        nota.asignatura?.nombre.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return notasFiltradas;
  };

  const getEstadoNota = (calificacion) => {
    if (calificacion >= 13) return { texto: 'Aprobado', color: 'green' };
    if (calificacion >= 10) return { texto: 'Recuperación', color: 'yellow' };
    return { texto: 'Desaprobado', color: 'red' };
  };

  const getColorNota = (calificacion) => {
    if (calificacion >= 13) return 'text-green-600';
    if (calificacion >= 10) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const notasFiltradas = getNotasFiltradas();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {asignaturaId && (
            <button
              onClick={() => navigate('/alumno/asignaturas')}
              className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
              <span>Volver a Asignaturas</span>
            </button>
          )}
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Mis Notas</h1>
      </div>

      {/* Estadísticas generales */}
      {promedioGeneral && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Promedio General</p>
                <p className="text-2xl font-semibold text-gray-900">{promedioGeneral.promedio}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FileText className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Notas</p>
                <p className="text-2xl font-semibold text-gray-900">{promedioGeneral.total_notas}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Award className="h-8 w-8 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Nota Máxima</p>
                <p className="text-2xl font-semibold text-gray-900">{promedioGeneral.nota_maxima}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BookOpen className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Nota Mínima</p>
                <p className="text-2xl font-semibold text-gray-900">{promedioGeneral.nota_minima}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filtrar por Asignatura
            </label>
            <select
              className="input-field"
              value={selectedAsignatura}
              onChange={(e) => setSelectedAsignatura(e.target.value)}
            >
              <option value="">Todas las asignaturas</option>
              {asignaturas.map((asignatura) => (
                <option key={asignatura.id} value={asignatura.id}>
                  {asignatura.nombre}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Buscar
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Buscar por asignatura..."
                className="input-field pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Tabla de notas */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Mis Calificaciones</h2>
        {notasFiltradas.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No hay notas registradas</h3>
            <p className="mt-1 text-sm text-gray-500">
              {selectedAsignatura ? 'No tienes notas en esta asignatura.' : 'Aún no tienes notas registradas.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Asignatura
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Docente
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tipo de Evaluación
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Calificación
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fecha
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {notasFiltradas.map((nota) => {
                  const estado = getEstadoNota(nota.calificacion);
                  return (
                    <tr key={nota.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {nota.asignatura?.nombre}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {nota.asignatura?.docente?.nombre_completo}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {nota.tipo_nota}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`font-semibold ${getColorNota(nota.calificacion)}`}>
                          {nota.calificacion}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          estado.color === 'green' ? 'bg-green-100 text-green-800' :
                          estado.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {estado.texto}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(nota.fecha_registro).toLocaleDateString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Promedios por asignatura */}
      {promediosPorAsignatura.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Promedios por Asignatura</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {promediosPorAsignatura.map((promedio) => (
              <div key={promedio.asignatura_id} className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-medium text-gray-900 mb-2">{promedio.asignatura_nombre}</h3>
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Promedio:</span>
                    <span className="font-semibold text-gray-900">{promedio.promedio}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Notas:</span>
                    <span className="text-gray-900">{promedio.total_notas}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Máxima:</span>
                    <span className="text-gray-900">{promedio.nota_maxima}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Mínima:</span>
                    <span className="text-gray-900">{promedio.nota_minima}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AlumnoNotas;

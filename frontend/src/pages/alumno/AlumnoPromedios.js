import React, { useState, useEffect } from 'react';
import { TrendingUp, Award, BookOpen, BarChart3 } from 'lucide-react';
import { alumnoService } from '../../services/alumnoService';

const AlumnoPromedios = () => {
  const [promedioGeneral, setPromedioGeneral] = useState(null);
  const [promediosPorAsignatura, setPromediosPorAsignatura] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [promedioData, promediosAsignaturaData] = await Promise.all([
        alumnoService.getMiPromedio(),
        alumnoService.getPromedioPorAsignatura()
      ]);
      
      setPromedioGeneral(promedioData);
      setPromediosPorAsignatura(promediosAsignaturaData);
    } catch (error) {
      console.error('Error al cargar datos:', error);
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (promedio) => {
    if (promedio >= 18) return 'text-green-600';
    if (promedio >= 14) return 'text-blue-600';
    if (promedio >= 11) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getGradeBgColor = (promedio) => {
    if (promedio >= 18) return 'bg-green-100';
    if (promedio >= 14) return 'bg-blue-100';
    if (promedio >= 11) return 'bg-yellow-100';
    return 'bg-red-100';
  };

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
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Mis Promedios</h1>
      </div>

      {/* Promedio General */}
      {promedioGeneral && (
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Promedio General</h2>
            <div className={`p-3 rounded-full ${getGradeBgColor(promedioGeneral.promedio)}`}>
              <TrendingUp className={`h-8 w-8 ${getGradeColor(promedioGeneral.promedio)}`} />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className={`text-4xl font-bold ${getGradeColor(promedioGeneral.promedio)}`}>
                {promedioGeneral.promedio}
              </div>
              <div className="text-sm text-gray-500">Promedio General</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{promedioGeneral.total_notas}</div>
              <div className="text-sm text-gray-500">Total Notas</div>
            </div>
            
            {promedioGeneral.nota_maxima && (
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{promedioGeneral.nota_maxima}</div>
                <div className="text-sm text-gray-500">Nota Máxima</div>
              </div>
            )}
            
            {promedioGeneral.nota_minima && (
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{promedioGeneral.nota_minima}</div>
                <div className="text-sm text-gray-500">Nota Mínima</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Promedios por Asignatura */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Promedios por Asignatura</h2>
          <BarChart3 className="h-6 w-6 text-gray-400" />
        </div>
        
        {promediosPorAsignatura.length === 0 ? (
          <div className="text-center py-8">
            <BookOpen className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No hay promedios disponibles</h3>
            <p className="mt-1 text-sm text-gray-500">
              No tienes notas registradas en ninguna asignatura.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {promediosPorAsignatura.map((promedio) => (
              <div key={promedio.asignatura_id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`p-2 rounded-lg ${getGradeBgColor(promedio.promedio)}`}>
                      <BookOpen className={`h-5 w-5 ${getGradeColor(promedio.promedio)}`} />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">{promedio.asignatura_nombre}</h3>
                      <p className="text-sm text-gray-500">{promedio.total_notas} nota(s) registrada(s)</p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${getGradeColor(promedio.promedio)}`}>
                      {promedio.promedio}
                    </div>
                    <div className="text-sm text-gray-500">Promedio</div>
                  </div>
                </div>
                
                {promedio.total_notas > 0 && (
                  <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Nota Máxima:</span>
                      <span className="font-medium text-green-600">{promedio.nota_maxima}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Nota Mínima:</span>
                      <span className="font-medium text-red-600">{promedio.nota_minima}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Leyenda de Colores */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Leyenda de Promedios</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-100 rounded"></div>
            <span className="text-sm text-gray-600">18-20 (Excelente)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-blue-100 rounded"></div>
            <span className="text-sm text-gray-600">14-17 (Bueno)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-100 rounded"></div>
            <span className="text-sm text-gray-600">11-13 (Regular)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-100 rounded"></div>
            <span className="text-sm text-gray-600">0-10 (Deficiente)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlumnoPromedios;

import React, { useState, useEffect } from 'react';
import { TrendingUp, Award, BookOpen, BarChart3 } from 'lucide-react';
import { alumnoService } from '../../services/alumnoService';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import api from '../../services/api';
import { drawHeader, drawInfoWithSeparator, autoTableTheme, drawFooter, fetchImageDataUrl } from '../../utils/pdfStyle';

const AlumnoPromedios = () => {
  const [promedioGeneral, setPromedioGeneral] = useState(null);
  const [promediosPorAsignatura, setPromediosPorAsignatura] = useState([]);
  const [notas, setNotas] = useState([]);
  const [loading, setLoading] = useState(true);
  // Nuevo: perfil, config y visor PDF
  const [perfil, setPerfil] = useState(null);
  const [config, setConfig] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [viewerOpen, setViewerOpen] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [promedioData, promediosAsignaturaData, notasData, perfilData, configData] = await Promise.all([
        alumnoService.getMiPromedio(),
        alumnoService.getPromedioPorAsignatura(true), // Solo ciclo actual
        alumnoService.getMisNotas(true), // Solo ciclo actual
        alumnoService.getMiPerfil(),
        api.get('/configuracion').then(r => r.data).catch(() => null)
      ]);
      
      setPromedioGeneral(promedioData);
      setPromediosPorAsignatura(promediosAsignaturaData);
      setNotas(notasData);
      setPerfil(perfilData);
      setConfig(configData);
    } catch (error) {
      console.error('Error al cargar datos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDescargarPromediosPDF = async () => {
    try {
      const doc = new jsPDF({ unit: 'mm', format: 'a4' });

      let logoDataUrl = null;
      try {
        if (config?.logo_url) {
          logoDataUrl = await fetchImageDataUrl(config.logo_url);
        }
      } catch (e) {
        console.warn('No fue posible obtener el logo desde la URL:', e);
      }

      const titulo = config?.nombre_sistema || 'Sistema de Notas';
      const subtitulo = 'Reporte: Promedios por Asignatura';
      const headerY = drawHeader(doc, { title: titulo, subtitle: subtitulo, logoDataUrl });

      const infoLines = [
        `Alumno: ${perfil?.nombre_completo || '-'}`,
        perfil?.ciclo ? `Ciclo: ${perfil.ciclo}` : null,
        `Fecha: ${new Date().toLocaleString()}`
      ].filter(Boolean);
      const nextY = drawInfoWithSeparator(doc, infoLines, headerY + 6);

      const head = [[
        'Asignatura',
        'Total Notas',
        'Promedio',
        'Nota Máxima',
        'Nota Mínima'
      ]];

      const body = (promediosPorAsignatura || []).map(p => [
        p.asignatura_nombre || '-',
        typeof p.total_notas === 'number' ? p.total_notas : String(p.total_notas || '-'),
        typeof p.promedio === 'number' ? Number(p.promedio).toFixed(2) : String(p.promedio || '-'),
        typeof p.nota_maxima === 'number' ? Number(p.nota_maxima).toFixed(2) : String(p.nota_maxima || '-'),
        typeof p.nota_minima === 'number' ? Number(p.nota_minima).toFixed(2) : String(p.nota_minima || '-')
      ]);

      autoTable(doc, {
        head,
        body,
        startY: nextY + 6,
        margin: { left: 14, right: 14 },
        ...autoTableTheme(),
        columnStyles: {
          0: { cellWidth: 70 },
          1: { cellWidth: 28, halign: 'center' },
          2: { cellWidth: 25, halign: 'right' },
          3: { cellWidth: 25, halign: 'right' },
          4: { cellWidth: 25, halign: 'right' }
        },
        didParseCell: (data) => {
          if (data.section === 'body' && data.column.index === 2) {
            const val = parseFloat(String(data.cell.raw).replace(',', '.'));
            if (!isNaN(val)) {
              if (val >= 18) data.cell.styles.textColor = [34, 197, 94]; // verde
              else if (val >= 14) data.cell.styles.textColor = [37, 99, 235]; // azul
              else if (val >= 11) data.cell.styles.textColor = [234, 179, 8]; // amarillo
              else data.cell.styles.textColor = [239, 68, 68]; // rojo
            }
          }
        },
        didDrawPage: drawFooter(doc)
      });

      const finalY = doc.lastAutoTable ? doc.lastAutoTable.finalY : nextY + 6;
      const total = (promediosPorAsignatura || []).length;
      doc.setFontSize(11);
      doc.setTextColor(33, 33, 33);
      doc.text(`Total asignaturas: ${total}`, 14, finalY + 8);

      const safeAlumno = (perfil?.nombre_completo || 'alumno').replace(/\s+/g, '_');
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[-:T]/g, '');
      const fileName = `Promedios_${safeAlumno}_${timestamp}.pdf`;

      const blob = doc.output('blob');
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
      setViewerOpen(true);

      // Fallback: si el visor falla, abrir en nueva pestaña
      const win = window.open(url, '_blank');
      if (!win) {
        doc.save(fileName);
      }
    } catch (error) {
      console.error('Error al visualizar el PDF de promedios:', error);
      alert('No se pudo generar y visualizar el PDF de promedios. Inténtalo más tarde.');
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

  const calcularPromediosDetallados = (asignaturaId) => {
    // Filtrar notas de la asignatura específica y solo notas publicadas
    const notasAsignatura = notas.filter(nota => 
      nota.asignatura_id === asignaturaId && nota.publicada
    );
    
    // Clasificar notas por tipo
    const actividades = notasAsignatura.filter(nota => 
      ['participacion', 'tarea', 'quiz', 'exposicion', 'laboratorio', 'trabajo_grupal'].includes(nota.tipo_nota)
    );
    
    const practicas = notasAsignatura.filter(nota => 
      nota.tipo_nota === 'practica'
    );
    
    const parciales = notasAsignatura.filter(nota => 
      nota.tipo_nota === 'examen_parcial'
    );
    
    const examenFinal = notasAsignatura.find(nota => 
      nota.tipo_nota === 'examen_final'
    );
    
    const proyectos = notasAsignatura.filter(nota => 
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Visor PDF modal */}
      {viewerOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-5xl">
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-600" />
                <span className="font-semibold">Vista previa PDF — Promedios por Asignatura</span>
              </div>
              <div className="flex items-center space-x-2">
                {pdfUrl && (
                  <a
                    href={pdfUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >Abrir en nueva pestaña</a>
                )}
                {pdfUrl && (
                  <a
                    href={pdfUrl}
                    download={`Promedios_${(perfil?.nombre_completo || 'alumno').replace(/\s+/g, '_')}.pdf`}
                    className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >Descargar</a>
                )}
                <button
                  onClick={() => { setViewerOpen(false); setPdfUrl(null); }}
                  className="px-3 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                >Cerrar</button>
              </div>
            </div>
            <div className="p-0">
              {pdfUrl ? (
                <iframe src={pdfUrl} title="Promedios PDF" className="w-full h-[75vh]" />
              ) : (
                <div className="p-6 text-center text-gray-500">Generando vista previa...</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Mis Promedios</h1>
      </div>

      {/* Promedio General - OCULTO */}
      {/* {promedioGeneral && (
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
      )} */}

      {/* Promedios por Asignatura */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Promedios por Asignatura</h2>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleDescargarPromediosPDF}
              className="btn-secondary px-3 py-1 text-xs"
              title="Ver promedios por asignatura en PDF"
            >
              Ver PDF
            </button>
            <BarChart3 className="h-6 w-6 text-gray-400" />
          </div>
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
          <div className="space-y-6">
            {promediosPorAsignatura.map((promedio) => {
              const promediosDetallados = calcularPromediosDetallados(promedio.asignatura_id);
              return (
                <div key={promedio.asignatura_id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                  {/* Header de la asignatura */}
                  <div className="flex items-center justify-between mb-4">
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
                      <div className={`text-2xl font-bold ${
                        promediosDetallados.promedioFinal >= 13 ? 'text-green-600' :
                        promediosDetallados.promedioFinal >= 10 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {promediosDetallados.promedioFinal > 0 ? promediosDetallados.promedioFinal.toFixed(2) : '-'}
                      </div>
                      <div className="text-sm text-gray-500">Promedio Final</div>
                    </div>
                  </div>
                  
                  {/* Estadísticas básicas */}
                  {promedio.total_notas > 0 && (
                    <div className="grid grid-cols-2 gap-4 text-sm">
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
              );
            })}
          </div>
        )}
      </div>

      {/* Leyenda de Colores - OCULTO */}
      {/* <div className="card">
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
      </div> */}
    </div>
  );
};

export default AlumnoPromedios;

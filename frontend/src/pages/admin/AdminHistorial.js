import React, { useState, useEffect } from 'react';
import { adminService } from '../../services/adminService';
import { Search, BookOpen, FileText, Trash2, X, ChevronDown, ChevronUp } from 'lucide-react';
import AdminHistorialAcademico from './AdminHistorialAcademico';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import api from '../../services/api';
import { drawHeader, drawInfoWithSeparator, autoTableTheme, drawFooter, fetchImageDataUrl } from '../../utils/pdfStyle';

const AdminHistorial = () => {
  const [alumnos, setAlumnos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAlumno, setSelectedAlumno] = useState(null);
  const [showHistorialModal, setShowHistorialModal] = useState(false);
  const [selectedCiclo, setSelectedCiclo] = useState(null);
  const [config, setConfig] = useState(null);
  const [years, setYears] = useState([]);
  const [selectedYear, setSelectedYear] = useState(null);
  const [registrosAnio, setRegistrosAnio] = useState([]);
  const [showYearList, setShowYearList] = useState(false);
  // Nuevo: visor PDF local para previsualización
  const [pdfUrl, setPdfUrl] = useState(null);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewerAlumno, setViewerAlumno] = useState(null);

  useEffect(() => {
    const fetchAlumnos = async () => {
      try {
        setLoading(true);
        const data = await adminService.getAlumnos();
        setAlumnos(data);
      } catch (error) {
        console.error('Error al cargar alumnos:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAlumnos();
  }, []);

  // Cargar configuración del sistema para obtener logo_url
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const resp = await api.get('/configuracion');
        setConfig(resp.data || null);
      } catch (e) {
        console.error('Error al cargar configuración:', e);
      }
    };
    fetchConfig();
  }, []);

  // Cargar años disponibles (vista por año)
  useEffect(() => {
    const fetchYears = async () => {
      try {
        const resp = await adminService.getHistorialYears();
        setYears(resp?.years || []);
      } catch (error) {
        console.error('Error al cargar años de historial:', error);
      }
    };
    fetchYears();
  }, []);

  // Cuando se selecciona un año, cargar los historiales de ese año
  useEffect(() => {
    const fetchPorAnio = async () => {
      if (!selectedYear) return;
      try {
        setLoading(true);
        const resp = await adminService.getHistorialPorAnio(selectedYear);
        const registros = (resp?.records || []).filter(r => !String(r.ciclo || '').includes('Ciclo Anterior'));
        setRegistrosAnio(registros);
        setSelectedCiclo(null);
        setSearchTerm('');
      } catch (error) {
        console.error('Error al cargar historiales por año:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchPorAnio();
  }, [selectedYear]);

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  // Contadores por ciclo
  const ciclosConContadoresAlumnos = alumnos.reduce((acc, alumno) => {
    const ciclo = alumno.ciclo;
    if (!ciclo) return acc;
    if (!acc[ciclo]) acc[ciclo] = 0;
    acc[ciclo]++;
    return acc;
  }, {});

  const ciclosConContadoresAnio = registrosAnio.reduce((acc, r) => {
    const ciclo = r.ciclo;
    if (!ciclo) return acc;
    if (!acc[ciclo]) acc[ciclo] = 0;
    acc[ciclo]++;
    return acc;
  }, {});

  const ciclos = Object.keys(selectedYear ? ciclosConContadoresAnio : ciclosConContadoresAlumnos).sort();

  const filteredAlumnos = alumnos.filter(alumno => {
    const matchesSearch =
      alumno.nombre_completo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      alumno.dni.includes(searchTerm) ||
      alumno.ciclo.toString().includes(searchTerm);
    const matchesCiclo = selectedCiclo ? alumno.ciclo === selectedCiclo : true;
    return matchesSearch && matchesCiclo;
  });

  const filteredRegistros = registrosAnio.filter(r => {
    const matchesSearch =
      String(r.alumno_nombre || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(r.dni || '').includes(searchTerm) ||
      String(r.ciclo || '').includes(searchTerm);
    const matchesCiclo = selectedCiclo ? r.ciclo === selectedCiclo : true;
    return matchesSearch && matchesCiclo;
  });

  const itemsParaTabla = selectedYear
    ? filteredRegistros.map(r => ({ id: r.alumno_id, nombre_completo: r.alumno_nombre, dni: r.dni }))
    : filteredAlumnos;

  const handleVerHistorial = (alumno) => {
    setSelectedAlumno(alumno);
    setShowHistorialModal(true);
  };

  const handleVerPdf = async (alumno) => {
    try {
      const data = await adminService.getHistorialAcademicoAlumno(alumno.id);

      let historial = (data || []).filter(item => !String(item.ciclo || '').includes('Ciclo Anterior'));
      // Si hay año/ciclo seleccionado, filtrar por ambos
      if (selectedYear) {
        historial = historial.filter(item => {
          const year = (() => {
            try {
              const d = new Date(item.fecha_registro);
              return isNaN(d.getTime()) ? String(item.fecha_registro).slice(0,4) : d.getFullYear();
            } catch (_) {
              return String(item.fecha_registro).slice(0,4);
            }
          })();
          return String(year) === String(selectedYear) && (!selectedCiclo || item.ciclo === selectedCiclo);
        });
      }

      historial = historial.map(item => ({
        ...item,
        ciclo: /^[IVX]+$/.test(String(item.ciclo)) ? `Ciclo: ${item.ciclo}` : item.ciclo
      }));

      if (!historial.length) {
        alert('No hay historial académico para este alumno con el filtro aplicado.');
        return;
      }

      const doc = new jsPDF({ unit: 'mm', format: 'a4' });

      let logoDataUrl = null;
      try {
        if (config?.logo_url) {
          logoDataUrl = await fetchImageDataUrl(config.logo_url);
        }
      } catch (e) {
        console.warn('No fue posible obtener el logo desde la URL:', e);
      }

      const subtitle = selectedYear
        ? `Historial Académico (${selectedYear}${selectedCiclo ? ` - Ciclo ${selectedCiclo}` : ''})`
        : 'Historial Académico';
      const headerY = drawHeader(doc, { title: (config?.nombre_sistema || 'Sistema de Notas').toUpperCase(), subtitle, logoDataUrl });
      const nextY = drawInfoWithSeparator(doc, [
        `Alumno: ${alumno.nombre_completo || ''}`,
        ...(alumno.dni ? [`DNI: ${alumno.dni}`] : [])
      ], headerY + 6);

      const marginLeft = 25 ;
      let y = nextY + 8;
      historial.forEach((ciclo) => {
        doc.setFontSize(11);
        doc.setTextColor(33, 33, 33);
        doc.text(String(ciclo.ciclo), marginLeft, y);
        y += 6;

        const rows = (ciclo.asignaturas || []).map(a => {
          const valor = a.promedio !== undefined && a.promedio !== null
            ? Number(a.promedio).toFixed(2)
            : (a.nota !== null && a.nota !== undefined ? a.nota : 'No registrada');
          const refer = a.promedio !== undefined && a.promedio !== null ? a.promedio : a.nota;
          const estado = refer !== null && refer !== undefined
            ? (Number(refer) >= 11 ? 'Aprobado' : 'Desaprobado')
            : 'Pendiente';
          return [a.nombre || '', valor, estado];
        });

        autoTable(doc, {
          startY: y,
          head: [['Asignatura', 'Nota', 'Estado']],
          body: rows,
          margin: { left: marginLeft, right: marginLeft },
          ...autoTableTheme(),
          styles: { fontSize: 10, cellPadding: 3 },
          columnStyles: {
            0: { cellWidth: 100 },
            1: { cellWidth: 25, halign: 'center' },
            2: { cellWidth: 35, halign: 'center' },
          },
          didDrawPage: drawFooter(doc)
        });
        y = (doc.lastAutoTable ? doc.lastAutoTable.finalY : y) + 12;
      });

      try {
        const blob = doc.output('blob');
        const url = URL.createObjectURL(blob);
        setPdfUrl(url);
        setViewerAlumno(alumno);
        setViewerOpen(true);
      } catch (e) {
        doc.save(`${alumno.nombre_completo || 'historial'}_historial.pdf`);
      }
    } catch (error) {
      console.error('Error al generar PDF:', error);
      alert('No se pudo generar el PDF del historial.');
    }
  };

  const handleEliminarHistorial = async (alumno) => {
    const confirmado = window.confirm(`¿Eliminar el historial académico de "${alumno.nombre_completo}"${selectedCiclo ? ` del ciclo ${selectedCiclo}` : ''}? Esto no eliminará al alumno, solo su historial.`);
    if (!confirmado) return;
    try {
      await adminService.deleteHistorialAcademicoAlumno(alumno.id, selectedYear ? selectedCiclo : null);
      if (showHistorialModal && selectedAlumno?.id === alumno.id) {
        setShowHistorialModal(false);
      }
      // Refrescar la lista si estamos en vista por año
      if (selectedYear) {
        const resp = await adminService.getHistorialPorAnio(selectedYear);
        const registros = (resp?.records || []).filter(r => !String(r.ciclo || '').includes('Ciclo Anterior'));
        setRegistrosAnio(registros);
      }
      alert('Historial académico eliminado correctamente.');
    } catch (error) {
      console.error('Error al eliminar historial académico:', error);
      alert('No se pudo eliminar el historial académico.');
    }
  };

  return (
    <div className="space-y-6">
      {viewerOpen && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h3 className="text-lg font-semibold">Historial Académico{selectedYear ? ` — ${selectedYear}${selectedCiclo ? ` • Ciclo ${selectedCiclo}` : ''}` : ''}</h3>
                <p className="text-sm text-gray-500">
                  Alumno: {viewerAlumno?.nombre_completo || '-'}{viewerAlumno?.dni ? ` • DNI: ${viewerAlumno.dni}` : ''}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                {pdfUrl && (
                  <a
                    href={pdfUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    title="Abrir en nueva pestaña"
                  >
                    Abrir en nueva pestaña
                  </a>
                )}
                {pdfUrl && (
                  <a
                    href={pdfUrl}
                    download={`Historial_${(viewerAlumno?.nombre_completo || 'alumno').replace(/\s+/g, '_')}${selectedYear ? `_${selectedYear}` : ''}${selectedCiclo ? `_Ciclo_${selectedCiclo}` : ''}.pdf`}
                    className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                    title="Descargar PDF"
                  >
                    Descargar
                  </a>
                )}
                <button
                  onClick={() => { if (pdfUrl) URL.revokeObjectURL(pdfUrl); setViewerOpen(false); setPdfUrl(null); setViewerAlumno(null); }}
                  className="px-3 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                  title="Cerrar visor"
                >
                  Cerrar
                </button>
              </div>
            </div>
            <div className="p-0">
              {pdfUrl ? (
                <iframe src={pdfUrl} title="Historial PDF" className="w-full h-[75vh]" />
              ) : (
                <div className="p-6 text-center text-gray-500">Generando vista previa...</div>
              )}
            </div>
          </div>
        </div>
      )}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Historial Académico</h1>
      </div>

      {/* Selector de años */}
      {!selectedYear ? (
        <div>
          <p className="text-gray-600 mb-3">Selecciona un año para ver los ciclos y alumnos.</p>
          <div className="flex items-center justify-between mb-3">
            <div className="relative inline-block">
              <button
                className="inline-flex items-center px-3 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
                onClick={() => setShowYearList(prev => !prev)}
              >
                {showYearList ? <ChevronUp className="h-4 w-4 mr-2" /> : <ChevronDown className="h-4 w-4 mr-2" />}
                Seleccionar año
              </button>
              {showYearList && (
                <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-max">
                  <div className="p-2">
                    {years.length === 0 ? (
                      <div className="text-sm text-gray-500 px-2 py-1">No hay años disponibles.</div>
                    ) : (
                      years.map((year) => (
                        <button
                          key={year}
                          className="block w-full text-left py-2 px-3 hover:bg-gray-50 rounded whitespace-nowrap"
                          onClick={() => { setSelectedYear(year); setSelectedCiclo(null); setSearchTerm(''); setShowYearList(false); }}
                          title={`Ver historiales del año ${year}`}
                        >
                          {year}
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Selector de ciclos (por año) */}
          {!selectedCiclo ? (
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="text-gray-600">Año seleccionado:</span>
                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm">{selectedYear}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="relative inline-block">
                    <button
                      className="inline-flex items-center px-3 py-1.5 bg-primary-600 text-white rounded hover:bg-primary-700"
                      onClick={() => setShowYearList(prev => !prev)}
                    >
                      {showYearList ? <ChevronUp className="h-4 w-4 mr-2" /> : <ChevronDown className="h-4 w-4 mr-2" />}
                      {`Seleccionar año: ${selectedYear}`}
                    </button>
                    {showYearList && (
                      <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-max">
                        <div className="p-2">
                          {years.length === 0 ? (
                            <div className="text-sm text-gray-500 px-2 py-1">No hay años disponibles.</div>
                          ) : (
                            years.map((year) => (
                              <button
                                key={year}
                                className="block w-full text-left py-2 px-3 hover:bg-gray-50 rounded whitespace-nowrap"
                                onClick={() => { setSelectedYear(year); setSelectedCiclo(null); setSearchTerm(''); setShowYearList(false); }}
                                title={`Ver historiales del año ${year}`}
                              >
                                {year}
                              </button>
                            ))
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  <button
                    className="text-blue-600 hover:text-blue-800"
                    onClick={() => { setSelectedYear(null); setSelectedCiclo(null); setSearchTerm(''); setShowYearList(false); }}
                  >
                    Ver todos los años
                  </button>
                </div>
              </div>
              <p className="text-gray-600 mb-3">Selecciona un ciclo del año {selectedYear}.</p>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {ciclos.map((ciclo) => (
                  <button
                    key={ciclo}
                    className="bg-white border border-gray-200 rounded-lg p-4 text-left hover:shadow transition-shadow"
                    onClick={() => { setSelectedCiclo(ciclo); setSearchTerm(''); }}
                    title={`Ver alumnos del Ciclo ${ciclo} en ${selectedYear}`}
                  >
                    <div className="text-xs text-gray-500">Ciclo</div>
                    <div className="text-xl font-semibold text-gray-900">{ciclo}</div>
                    <div className="text-xs text-gray-500">{(selectedYear ? ciclosConContadoresAnio[ciclo] : ciclosConContadoresAlumnos[ciclo])} alumnos</div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-gray-600">Año:</span>
                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm">{selectedYear}</span>
                  <span className="text-gray-600 ml-3">Ciclo:</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">{selectedCiclo}</span>
                </div>
                <button
                  className="text-blue-600 hover:text-blue-800"
                  onClick={() => { setSelectedCiclo(null); setSearchTerm(''); }}
                >
                  Ver ciclos del año
                </button>
              </div>

              {/* Buscador */}
              <div className="relative mt-4">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Buscar por nombre, DNI..."
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  value={searchTerm}
                  onChange={handleSearch}
                />
              </div>
            </>
          )}
        </>
      )}

      {/* Lista de alumnos filtrada */}
      {selectedYear && selectedCiclo && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="flex justify-center items-center h-40">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500"></div>
            </div>
          ) : itemsParaTabla.length === 0 ? (
            <div className="text-center py-10">
              <p className="text-gray-500">No hay alumnos en el Ciclo {selectedCiclo} del año {selectedYear}{searchTerm ? ' que coincidan con la búsqueda' : ''}.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Nombre
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      DNI
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {itemsParaTabla.map((alumno) => (
                    <tr key={alumno.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {alumno.nombre_completo}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {alumno.dni}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex items-center space-x-4">
                          <button
                            onClick={() => handleVerPdf(alumno)}
                            className="text-rose-600 hover:text-rose-800 flex items-center"
                            title="Ver historial en PDF"
                          >
                            <FileText className="h-4 w-4 mr-1" />
                            Ver
                          </button>
                          <button
                            onClick={() => handleEliminarHistorial(alumno)}
                            className="text-red-600 hover:text-red-800 flex items-center"
                            title="Eliminar historial académico del ciclo"
                          >
                            <Trash2 className="h-4 w-4 mr-1" />
                            Eliminar
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Modal para ver historial académico */}
      {showHistorialModal && selectedAlumno && (
        <AdminHistorialAcademico 
          alumno={selectedAlumno} 
          onClose={() => setShowHistorialModal(false)} 
        />
      )}
    </div>
  );
};

export default AdminHistorial;
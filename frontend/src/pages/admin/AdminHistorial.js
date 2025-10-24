import React, { useState, useEffect } from 'react';
import { adminService } from '../../services/adminService';
import { Search, BookOpen, FileText, Trash2, X } from 'lucide-react';
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

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  // Ciclos únicos con contador de alumnos por ciclo
  const ciclosConContadores = alumnos.reduce((acc, alumno) => {
    const ciclo = alumno.ciclo;
    if (!ciclo) return acc;
    if (!acc[ciclo]) acc[ciclo] = 0;
    acc[ciclo]++;
    return acc;
  }, {});

  const ciclos = Object.keys(ciclosConContadores).sort();

  const filteredAlumnos = alumnos.filter(alumno => {
    const matchesSearch =
      alumno.nombre_completo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      alumno.dni.includes(searchTerm) ||
      alumno.ciclo.toString().includes(searchTerm);
    const matchesCiclo = selectedCiclo ? alumno.ciclo === selectedCiclo : true;
    return matchesSearch && matchesCiclo;
  });

  const handleVerHistorial = (alumno) => {
    setSelectedAlumno(alumno);
    setShowHistorialModal(true);
  };

  const handleVerPdf = async (alumno) => {
    try {
      const data = await adminService.getHistorialAcademicoAlumno(alumno.id);

      // Filtrar entradas de "Ciclo Anterior" y formatear ciclo
      const filtered = (data || []).filter(item => !String(item.ciclo || '').includes('Ciclo Anterior'));
      const historial = filtered.map(item => ({
        ...item,
        ciclo: /^[IVX]+$/.test(String(item.ciclo)) ? `Ciclo: ${item.ciclo}` : item.ciclo
      }));

      if (!historial.length) {
        alert('No hay historial académico para este alumno.');
        return;
      }

      const doc = new jsPDF({ unit: 'pt', format: 'a4' });

      // Preparar logo si hay URL en configuración
      let logoDataUrl = null;
      try {
        if (config?.logo_url) {
          logoDataUrl = await fetchImageDataUrl(config.logo_url);
        }
      } catch (e) {
        console.warn('No fue posible obtener el logo desde la URL:', e);
      }

      const headerY = drawHeader(doc, { title: (config?.nombre_sistema || 'Sistema de Notas'), subtitle: 'Historial Académico', logoDataUrl });
      const nextY = drawInfoWithSeparator(doc, [
        `Alumno: ${alumno.nombre_completo || ''}`,
        ...(alumno.dni ? [`DNI: ${alumno.dni}`] : [])
      ], headerY + 6);

      const marginLeft = 40;
      let y = nextY + 12;
      historial.forEach((ciclo) => {
        doc.setFontSize(12);
        doc.text(String(ciclo.ciclo), marginLeft, y);
        y += 10;

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
          ...autoTableTheme(),
          styles: { fontSize: 10, cellPadding: 4 },
          margin: { left: marginLeft, right: marginLeft },
          didDrawPage: drawFooter(doc)
        });
        y = doc.lastAutoTable.finalY + 18;
      });

      try {
        const blobUrl = doc.output('bloburl');
        const win = window.open(blobUrl, '_blank');
        if (!win) doc.save(`${alumno.nombre_completo || 'historial'}_historial.pdf`);
      } catch (e) {
        doc.save(`${alumno.nombre_completo || 'historial'}_historial.pdf`);
      }
    } catch (error) {
      console.error('Error al generar PDF:', error);
      alert('No se pudo generar el PDF del historial.');
    }
  };

  const handleEliminarHistorial = async (alumno) => {
    const confirmado = window.confirm(`¿Eliminar el historial académico de "${alumno.nombre_completo}"? Esto no eliminará al alumno, solo su historial.`);
    if (!confirmado) return;
    try {
      await adminService.deleteHistorialAcademicoAlumno(alumno.id);
      if (showHistorialModal && selectedAlumno?.id === alumno.id) {
        setShowHistorialModal(false);
      }
      alert('Historial académico eliminado correctamente.');
    } catch (error) {
      console.error('Error al eliminar historial académico:', error);
      alert('No se pudo eliminar el historial académico.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Historial Académico</h1>
      </div>

      {/* Selector de ciclos */}
      {!selectedCiclo ? (
        <div>
          <p className="text-gray-600 mb-3">Selecciona un ciclo para ver los alumnos y su historial académico.</p>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {ciclos.map((ciclo) => (
              <button
                key={ciclo}
                className="bg-white border border-gray-200 rounded-lg p-4 text-left hover:shadow transition-shadow"
                onClick={() => { setSelectedCiclo(ciclo); setSearchTerm(''); }}
                title={`Ver alumnos del Ciclo ${ciclo}`}
              >
                <div className="text-xs text-gray-500">Ciclo</div>
                <div className="text-xl font-semibold text-gray-900">{ciclo}</div>
                <div className="text-xs text-gray-500">{ciclosConContadores[ciclo]} alumnos</div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-gray-600">Ciclo seleccionado:</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">{selectedCiclo}</span>
            </div>
            <button
              className="text-blue-600 hover:text-blue-800"
              onClick={() => { setSelectedCiclo(null); setSearchTerm(''); }}
            >
              Ver todos los ciclos
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

      {/* Lista de alumnos por ciclo: solo mostrar cuando hay ciclo seleccionado */}
      {selectedCiclo && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="flex justify-center items-center h-40">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500"></div>
            </div>
          ) : filteredAlumnos.length === 0 ? (
            <div className="text-center py-10">
              <p className="text-gray-500">No hay alumnos en el Ciclo {selectedCiclo}{searchTerm ? ' que coincidan con la búsqueda' : ''}.</p>
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
                  {filteredAlumnos.map((alumno) => (
                    <tr key={alumno.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {alumno.nombre_completo}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {alumno.dni}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex items-center space-x-4">
                          {/* <button
                            onClick={() => handleVerHistorial(alumno)}
                            className="text-blue-600 hover:text-blue-900 flex items-center"
                            title="Ver historial académico"
                          >
                            <BookOpen className="h-4 w-4 mr-1" />
                            Ver historial
                          </button> */}
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
                            title="Eliminar historial académico"
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
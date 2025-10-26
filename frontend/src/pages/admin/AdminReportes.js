import React, { useEffect, useState } from 'react';
import { BarChart, FileSpreadsheet, FileText, Download, Eye, Trash, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { drawHeader, drawInfoWithSeparator, autoTableTheme, drawFooter, fetchImageDataUrl } from '../../utils/pdfStyle';

const AdminReportes = () => {
  const navigate = useNavigate();
  const [reportes, setReportes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [config, setConfig] = useState(null);
  // Visor PDF modal
  const [pdfUrl, setPdfUrl] = useState(null);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [selectedReporte, setSelectedReporte] = useState(null);

  useEffect(() => { 
    const fetchReportes = async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await api.get('/admin/reportes');
        setReportes(resp.data || []);
      } catch (err) {
        console.error('Error al cargar reportes:', err);
        setError('No se pudieron cargar los reportes.');
      } finally {
        setLoading(false);
      }
    };
    fetchReportes();
  }, []);

  // Cargar configuración del sistema (incluye logo_url)
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

  const handleVer = async (reporte) => {
    try {
      const resp = await api.get(`/admin/reportes/${reporte.id}/archivo`, { responseType: 'blob' });

      // Determinar tipo de archivo por Content-Type o por extensión del nombre
      const contentType = (resp.headers && (resp.headers['content-type'] || resp.headers['Content-Type'])) || '';
      const nombre = reporte.archivo_path?.split('\\').pop() || reporte.archivo_path?.split('/').pop() || '';
      const ext = (nombre && nombre.includes('.')) ? nombre.split('.').pop().toLowerCase() : '';

      // Si es un PDF ya generado por el docente, abrirlo en visor interno
      if (contentType.includes('pdf') || ext === 'pdf') {
        const url = window.URL.createObjectURL(resp.data);
        setPdfUrl(url);
        setSelectedReporte(reporte);
        setViewerOpen(true);
        return;
      }

      // Caso contrario, asumimos CSV y lo convertimos a PDF para visualizar
      const blobToText = (blob) => {
        if (blob && typeof blob.text === 'function') {
          return blob.text();
        }
        return new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result);
          reader.onerror = reject;
          reader.readAsText(blob);
        });
      };

      const text = await blobToText(resp.data);
      const normalized = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
      const lines = normalized.split('\n').filter(l => l.trim().length > 0);
      if (lines.length === 0) {
        alert('El reporte está vacío.');
        return;
      }
      const firstLine = lines[0];
      const delimiter = firstLine.includes(';') ? ';' : (firstLine.includes('\t') ? '\t' : ',');
      const rawHeaders = firstLine.split(delimiter).map(h => h.trim());
      const rawRows = lines.slice(1).map(line => line.split(delimiter).map(c => c.trim()));

      // Reordenar columnas a un estándar común (referencia DocenteReportes)
      const idxAlumno = rawHeaders.findIndex(h => /alumn|estudiant|nombre/i.test(h));
      const idxCiclo = rawHeaders.findIndex(h => /ciclo|grado|nivel/i.test(h));
      const idxAsignatura = rawHeaders.findIndex(h => /asignatura|curso/i.test(h));
      const idxTipo = rawHeaders.findIndex(h => /tipo.*evalu|evaluaci[oó]n|tipo/i.test(h));
      const idxCalificacion = rawHeaders.findIndex(h => /calific|nota|puntaje/i.test(h));

      const orderedDefs = [
        { idx: idxAlumno, label: 'Alumno' },
        { idx: idxCiclo, label: 'Ciclo' },
        { idx: idxAsignatura, label: 'Asignatura' },
        { idx: idxTipo, label: 'Tipo de Evaluación' },
        { idx: idxCalificacion, label: 'Calificación' },
      ].filter(d => d.idx >= 0);
      const remainingIndices = rawHeaders.map((_, i) => i).filter(i => !orderedDefs.some(d => d.idx === i));
      const headers = [...orderedDefs.map(d => d.label), ...remainingIndices.map(i => rawHeaders[i])];
      const rows = rawRows.map(r => [
        ...orderedDefs.map(d => r[d.idx] || ''),
        ...remainingIndices.map(i => r[i] || ''),
      ]);

      const doc = new jsPDF({ unit: 'mm', format: 'a4' });

      // Preparar logo si hay URL en configuración
      let logoDataUrl = null;
      try {
        if (config?.logo_url) {
          logoDataUrl = await fetchImageDataUrl(config.logo_url);
        }
      } catch (e) {
        console.warn('No fue posible obtener el logo desde la URL:', e);
      }

      const headerY = drawHeader(doc, {
        title: config?.nombre_sistema || 'Sistema de Notas',
        subtitle: `Reporte: ${reporte.tipo_evaluacion || '-' } - ${reporte.asignatura || '-'}`,
        logoDataUrl
      });
      const nextY = drawInfoWithSeparator(doc, [
        `Docente: ${reporte.nombre_docente || '-'}`,
        `Fecha: ${new Date(reporte.fecha_envio).toLocaleString()}`
      ], headerY + 6);

      autoTable(doc, {
        startY: nextY + 6,
        head: [headers],
        body: rows,
        ...autoTableTheme(),
        margin: { left: 14, right: 14 },
        columnStyles: {
          0: { cellWidth: 60 },
          1: { cellWidth: 16, halign: 'center' },
          2: { cellWidth: 40, halign:"center" },
          3: { cellWidth: 35, halign:"center" },
          4: { cellWidth: 30, halign: 'center' }
        },
        didParseCell: (data) => {
          const gradeColIdx = headers.findIndex(h => /calific/i.test(h) || h === 'Calificación');
          if (data.section === 'body' && data.column.index === gradeColIdx) {
            const rawText = Array.isArray(data.cell.text) ? data.cell.text.join(' ') : String(data.cell.text || data.cell.raw || '');
            const normalizedText = rawText.replace(',', '.');
            const match = normalizedText.match(/-?\d+(?:\.\d+)?/);
            const grade = match ? parseFloat(match[0]) : NaN;
            if (!Number.isNaN(grade)) {
              if (grade >= 13 && grade <= 20) {
                data.cell.styles.textColor = [34, 197, 94];
              } else if (grade >= 10 && grade < 13) {
                data.cell.styles.textColor = [234, 179, 8];
              } else if (grade >= 5 && grade < 10) {
                data.cell.styles.textColor = [239, 68, 68];
              }
            }
          }
        },
        didDrawPage: drawFooter(doc)
      });

      // Totales simples al pie
      const finalY = doc.lastAutoTable ? doc.lastAutoTable.finalY : (nextY + 6);
      const total = rows.length;
      doc.setFontSize(11);
      doc.setTextColor(33, 33, 33);
      doc.text(`Total alumnos: ${total}`, 14, finalY + 8);

      const blob = doc.output('blob');
      const url = window.URL.createObjectURL(blob);
      setPdfUrl(url);
      setSelectedReporte(reporte);
      setViewerOpen(true);
    } catch (err) {
      console.error('Error al generar PDF:', err);
      alert('No fue posible generar el PDF del reporte.');
    }
  };

  const handleEliminar = async (reporte) => {
    const confirmar = window.confirm('¿Seguro que deseas eliminar este reporte? Esta acción no se puede deshacer.');
    if (!confirmar) return;
    try {
      await api.delete(`/admin/reportes/${reporte.id}`);
      setReportes((prev) => prev.filter((x) => x.id !== reporte.id));
    } catch (err) {
      console.error('Error al eliminar reporte:', err);
      alert('No fue posible eliminar el reporte.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Modal visor PDF */}
      {viewerOpen && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h3 className="text-lg font-semibold">Reporte: {selectedReporte?.tipo_evaluacion} - {selectedReporte?.asignatura}</h3>
                <p className="text-sm text-gray-500">Docente: {selectedReporte?.nombre_docente} • Fecha: {selectedReporte ? new Date(selectedReporte.fecha_envio).toLocaleString() : ''}</p>
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
                    download={`Reporte_${(selectedReporte?.asignatura || 'asignatura').replace(/\s+/g, '_')}_${(selectedReporte?.tipo_evaluacion || 'evaluacion').replace(/\s+/g, '_')}.pdf`}
                    className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >Descargar</a>
                )}
                <button
                  onClick={() => { setViewerOpen(false); setPdfUrl(null); setSelectedReporte(null); }}
                  className="px-3 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 inline-flex items-center"
                >
                  <X className="mr-1 h-4 w-4" /> Cerrar
                </button>
              </div>
            </div>
            <div className="p-0">
              {pdfUrl ? (
                <iframe src={pdfUrl} title="Reporte PDF" className="w-full h-[75vh]" />
              ) : (
                <div className="p-6 text-center text-gray-500">Generando vista previa...</div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <BarChart className="mr-3 h-6 w-6 text-blue-600" />
          <h1 className="text-2xl font-semibold">Reportes</h1>
        </div>
        <p className="text-gray-600">
          Panel de reportes . Aquí podrás recibir los reportes del Docente .
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        

        
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Reportes enviados por docentes</h2>
          {loading && <span className="text-sm text-gray-500">Cargando...</span>}
        </div>
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 mb-4">
            {error}
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Docente</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asignatura</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo evaluación</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha envío</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reportes.length === 0 ? (
                <tr>
                  <td className="px-6 py-4 text-sm text-gray-500" colSpan="5">
                    No hay reportes enviados aún.
                  </td>
                </tr>
              ) : (
                reportes.map((r) => (
                  <tr key={r.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{r.nombre_docente}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{r.asignatura}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{r.tipo_evaluacion}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{new Date(r.fecha_envio).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <button
                        className="inline-flex items-center px-3 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
                        onClick={() => handleVer(r)}
                        title="Ver"
                      >
                        <Eye className="mr-2 h-4 w-4" /> Ver
                      </button>
                      <button
                        className="inline-flex items-center px-3 py-2 rounded bg-red-600 text-white hover:bg-red-700"
                        onClick={() => handleEliminar(r)}
                        title="Eliminar reporte"
                      >
                        <Trash className="mr-2 h-4 w-4" /> Eliminar
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminReportes;
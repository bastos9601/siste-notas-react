import api from './api';
import * as XLSX from 'xlsx';

export const adminService = {
  // Gestión de Alumnos
  async getAlumnos() {
    const response = await api.get('/admin/alumnos');
    return response.data;
  },

  async createAlumno(alumnoData) {
    const response = await api.post('/admin/alumnos', alumnoData);
    return response.data;
  },

  async getAlumno(id) {
    const response = await api.get(`/admin/alumnos/${id}`);
    return response.data;
  },

  async updateAlumno(id, alumnoData) {
    const response = await api.put(`/admin/alumnos/${id}`, alumnoData);
    return response.data;
  },

  async deleteAlumno(id) {
    const response = await api.delete(`/admin/alumnos/${id}`);
    return response.data;
  },

  async enviarContrasenaAlumno(id) {
    const response = await api.post(`/admin/alumnos/${id}/enviar-contrasena`);
    return response.data;
  },
  
  // Importación CSV de alumnos
  async importarAlumnosCSV(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/admin/alumnos/import-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Importación Excel de alumnos (convertimos Excel -> CSV y reutilizamos el endpoint CSV)
  async importarAlumnosExcel(file) {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const workbook = XLSX.read(arrayBuffer, { type: 'array' });

      // Heurística: elegir la hoja con mejores encabezados esperados
      const normalize = (s) => {
        if (!s) return '';
        const t = String(s).normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
        return t.toLowerCase().replace(/[_.;:\-]+/g, ' ').replace(/\s+/g, ' ').trim();
      };
      const expected = [
        ['dni', 'documento', 'numero documento', 'cedula'],
        ['email', 'correo', 'correo electronico', 'mail', 'e mail'],
        ['ciclo', 'semestre', 'nivel', 'periodo'],
        ['nombre completo', 'nombres y apellidos', 'nombre y apellidos', 'alumno', 'estudiante']
      ];
      const scoreHeaders = (headerRow) => {
        const normSet = new Set(headerRow.map((h) => normalize(h)));
        let score = 0;
        for (const group of expected) {
          for (const cand of group) {
            if (normSet.has(normalize(cand))) { score++; break; }
          }
        }
        return score;
      };

      let bestSheetName = workbook.SheetNames[0];
      let bestScore = -1;
      for (const name of workbook.SheetNames) {
        const sheet = workbook.Sheets[name];
        const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, blankrows: false });
        const header = rows[0] || [];
        const s = scoreHeaders(Array.isArray(header) ? header : []);
        if (s > bestScore) { bestScore = s; bestSheetName = name; }
      }
      const sheet = workbook.Sheets[bestSheetName];

      // Convertir a CSV evitando filas en blanco
      const csvText = XLSX.utils.sheet_to_csv(sheet, { FS: ',', RS: '\n', blankrows: false });

      // Crear un File/Blob CSV para enviarlo al backend
      const csvBlob = new Blob([csvText], { type: 'text/csv' });
      const csvFile = new File([csvBlob], `${(file.name || 'import')}.csv`, { type: 'text/csv' });

      return await adminService.importarAlumnosCSV(csvFile);
    } catch (err) {
      // Fallback: enviar excel al endpoint original si la conversión falla
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post('/admin/alumnos/import-excel', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    }
  },
  // Registrar siguiente ciclo (no matricular, solo actualizar campo ciclo)
  async registrarSiguienteCicloAlumno(id) {
    const response = await api.post(`/admin/alumnos/${id}/registrar-siguiente-ciclo`);
    return response.data;
  },

  async registrarSiguienteCicloTodos() {
    const response = await api.post(`/admin/matricula-automatica/todos`);
    return response.data;
  },

  // Gestión de Docentes
  async getDocentes() {
    const response = await api.get('/admin/docentes');
    return response.data;
  },

  async createDocente(docenteData) {
    const response = await api.post('/admin/docentes', docenteData);
    return response.data;
  },

  async getDocente(id) {
    const response = await api.get(`/admin/docentes/${id}`);
    return response.data;
  },

  async updateDocente(id, docenteData) {
    const response = await api.put(`/admin/docentes/${id}`, docenteData);
    return response.data;
  },

  async deleteDocente(id) {
    const response = await api.delete(`/admin/docentes/${id}`);
    return response.data;
  },

  async enviarContrasenaDocente(id) {
    const response = await api.post(`/admin/docentes/${id}/enviar-contrasena`);
    return response.data;
  },

  // Gestión de Asignaturas
  async getAsignaturas(ciclo = null) {
    const url = ciclo ? `/admin/asignaturas?ciclo=${ciclo}` : '/admin/asignaturas';
    const response = await api.get(url);
    return response.data;
  },

  async createAsignatura(asignaturaData) {
    const response = await api.post('/admin/asignaturas', asignaturaData);
    return response.data;
  },

  async getAsignatura(id) {
    const response = await api.get(`/admin/asignaturas/${id}`);
    return response.data;
  },

  async updateAsignatura(id, asignaturaData) {
    const response = await api.put(`/admin/asignaturas/${id}`, asignaturaData);
    return response.data;
  },

  async deleteAsignatura(id) {
    const response = await api.delete(`/admin/asignaturas/${id}`);
    return response.data;
  },

  // Gestión de Matrículas
  async getMatriculas() {
    const response = await api.get('/admin/matriculas');
    return response.data;
  },

  async createMatricula(matriculaData) {
    const response = await api.post('/admin/matriculas', matriculaData);
    return response.data;
  },
  
  async deleteMatricula(alumnoId, asignaturaId) {
    const response = await api.delete(`/admin/matriculas/${alumnoId}/${asignaturaId}`);
    return response.data;
  },
  
  // Gestión de Notas
  async getNotas() {
    const response = await api.get('/admin/notas');
    return response.data;
  },

  // Dashboard
  async getDashboard() {
    const response = await api.get('/admin/dashboard');
    return response.data;
  },

  // Mi Perfil
  async actualizarMiPerfil(perfilData) {
    const response = await api.put('/admin/mi-perfil', perfilData);
    return response.data;
  },

  // Historial Académico
  async getHistorialAcademicoAlumno(alumnoId) {
    const response = await api.get(`/historial/alumnos/${alumnoId}/historial`);
    return response.data;
  },

  // Nuevo: años disponibles de historiales
  async getHistorialYears() {
    const response = await api.get('/historial/years');
    return response.data;
  },

  // Nuevo: historiales por año (resumen por alumno y ciclo)
  async getHistorialPorAnio(year) {
    const response = await api.get(`/historial/por-anio/${year}`);
    return response.data;
  },
  
  async deleteHistorialAcademicoAlumno(alumnoId, ciclo = null) {
    const url = ciclo 
      ? `/historial/alumnos/${alumnoId}/historial?ciclo=${encodeURIComponent(ciclo)}`
      : `/historial/alumnos/${alumnoId}/historial`;
    const response = await api.delete(url);
    return response.data;
  },
  
  // Configuración del sistema
  async getConfiguracionPublica() {
    const response = await api.get('/configuracion');
    return response.data;
  },

  async actualizarConfiguracion(configData) {
    const response = await api.put('/admin/configuracion', configData);
    return response.data;
  },

  async subirLogo(file) {
    const formData = new FormData();
    formData.append('archivo', file);
    const response = await api.post('/admin/configuracion/logo/cloudinary', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
};

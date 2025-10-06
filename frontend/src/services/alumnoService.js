import api from './api';

export const alumnoService = {
  // Asignaturas del alumno
  async getMisAsignaturas() {
    const response = await api.get('/alumno/mis-asignaturas');
    return response.data;
  },

  // Notas del alumno
  async getMisNotas() {
    const response = await api.get('/alumno/mis-notas');
    return response.data;
  },

  async getNotasPorAsignatura(asignaturaId) {
    const response = await api.get(`/alumno/asignaturas/${asignaturaId}/notas`);
    return response.data;
  },

  // Promedios
  async getMiPromedio() {
    const response = await api.get('/alumno/promedio');
    return response.data;
  },

  async getPromedioPorAsignatura() {
    const response = await api.get('/alumno/promedio-por-asignatura');
    return response.data;
  },

  // Perfil
  async getMiPerfil() {
    const response = await api.get('/alumno/perfil');
    return response.data;
  },

  async cambiarContrasena(contrasenaData) {
    const response = await api.put('/alumno/cambiar-contrasena', contrasenaData);
    return response.data;
  }
};

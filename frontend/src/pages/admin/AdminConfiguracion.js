import React, { useEffect, useState } from 'react';
import { adminService } from '../../services/adminService';
import { UploadCloud, Save, Image as ImageIcon, Settings, Moon, Sun } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

const AdminConfiguracion = () => {
  const [nombreSistema, setNombreSistema] = useState('');
  const [logoUrl, setLogoUrl] = useState('');
  const [modoOscuro, setModoOscuro] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const { isDark, setDark } = useTheme();

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const config = await adminService.getConfiguracionPublica();
        setNombreSistema(config?.nombre_sistema || 'Sistema de Gestión de Notas');
        setLogoUrl(config?.logo_url || '');
        if (typeof config?.modo_oscuro === 'boolean') {
          setModoOscuro(config.modo_oscuro);
          setDark(config.modo_oscuro);
        } else {
          setModoOscuro(isDark);
        }
      } catch (e) {
        console.error('Error al cargar configuración:', e);
        setError('No se pudo cargar la configuración.');
      } finally {
        setLoading(false);
      }
    };
    loadConfig();
  }, []);

  const handleUploadLogo = async (file) => {
    if (!file) return;
    try {
      setUploading(true);
      setError('');
      setMessage('');
      const { url } = await adminService.subirLogo(file);
      if (url) {
        setLogoUrl(url);
        setMessage('Logo subido correctamente a Cloudinary.');
      } else {
        setError('No se pudo subir el logo a Cloudinary.');
      }
    } catch (e) {
      console.error('Error subiendo el logo:', e);
      setError('Ocurrió un error al subir el logo.');
    } finally {
      setUploading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError('');
      setMessage('');
      const updated = await adminService.actualizarConfiguracion({
        nombre_sistema: nombreSistema,
        logo_url: logoUrl || null,
        modo_oscuro: modoOscuro,
      });
      setNombreSistema(updated.nombre_sistema);
      setLogoUrl(updated.logo_url || '');
      setModoOscuro(!!updated.modo_oscuro);
      setDark(!!updated.modo_oscuro);
      setMessage('Configuración guardada.');
    } catch (e) {
      console.error('Error guardando configuración:', e);
      setError('No se pudo guardar la configuración.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse h-6 bg-gray-200 rounded w-48 mb-4" />
        <div className="animate-pulse h-40 bg-gray-200 rounded" />
      </div>
    );
  }

  // Eliminar dependencia de variables de entorno del cliente
  // const cloudConfigured = !!(process.env.REACT_APP_CLOUDINARY_CLOUD_NAME && process.env.REACT_APP_CLOUDINARY_UPLOAD_PRESET);

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Settings className="w-6 h-6 text-blue-600" />
        <h1 className="text-2xl font-semibold">Configuración del Sistema</h1>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded">{error}</div>
      )}
      {message && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded">{message}</div>
      )}

      <div className="bg-white rounded-lg shadow p-5 border border-gray-200 dark:bg-gray-800 dark:border-gray-700">
        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-2 dark:text-gray-200">Nombre del sistema</label>
          <input
            type="text"
            value={nombreSistema}
            onChange={(e) => setNombreSistema(e.target.value)}
            className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100"
            placeholder="Ej. Sistema de Gestión de Notas"
          />
        </div>

        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-2 dark:text-gray-200">Logo del sistema</label>
          <div className="flex items-center gap-4">
            <div className="w-32 h-32 border rounded flex items-center justify-center bg-gray-50 dark:bg-gray-900 dark:border-gray-700">
              {logoUrl ? (
                <img src={logoUrl} alt="Logo" className="max-w-full max-h-full object-contain" />
              ) : (
                <ImageIcon className="w-10 h-10 text-gray-400" />
              )}
            </div>
            <div>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => handleUploadLogo(e.target.files?.[0])}
                disabled={uploading}
                className="block text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">
                {'El archivo se sube a Cloudinary y se guarda solo el URL.'}
              </p>
            </div>
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2 dark:text-gray-200">Modo oscuro</label>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => { const v = !modoOscuro; setModoOscuro(v); setDark(v); }}
              className="inline-flex items-center gap-2 px-3 py-2 rounded border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              {modoOscuro ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
              <span>{modoOscuro ? 'Activado' : 'Desactivado'}</span>
            </button>
            <span className="text-xs text-gray-500">Aplica tema oscuro a toda la interfaz.</span>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-60"
          >
            <Save className="w-4 h-4" /> Guardar
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminConfiguracion;
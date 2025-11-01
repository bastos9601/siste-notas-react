import React, { useState } from 'react';
import { Download } from 'lucide-react';

const DownloadTemplateButton = ({ 
  fileName = 'Template.xlsx', 
  buttonText = 'Descargar Plantilla',
  className = '',
  variant = 'secondary' // 'primary', 'secondary', 'outline'
}) => {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      
      // Fetch del archivo desde la carpeta public/templates
      const response = await fetch(`/templates/${fileName}`);
      
      if (!response.ok) {
        throw new Error('Error al descargar el archivo');
      }
      
      // Convertir a blob
      const blob = await response.blob();
      
      // Crear URL del blob
      const url = window.URL.createObjectURL(blob);
      
      // Crear link de descarga
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      
      // Ejecutar descarga
      document.body.appendChild(link);
      link.click();
      
      // Limpiar
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Error al descargar:', error);
      alert('Error al descargar el archivo. Por favor, intenta nuevamente.');
    } finally {
      setIsDownloading(false);
    }
  };

  // Definir clases según la variante
  const getButtonClasses = () => {
    const baseClasses = `inline-flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors duration-200 ${className}`;
    
    switch (variant) {
      case 'primary':
        return `${baseClasses} bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400`;
      case 'outline':
        return `${baseClasses} border border-blue-600 text-blue-600 hover:bg-blue-50 disabled:border-blue-400 disabled:text-blue-400`;
      case 'secondary':
      default:
        return `${baseClasses} bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400`;
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={isDownloading}
      className={getButtonClasses()}
      title={`Descargar ${fileName}`}
    >
      <Download className="h-4 w-4 mr-2" />
      {isDownloading ? 'Descargando...' : buttonText}
    </button>
  );
};

export default DownloadTemplateButton;
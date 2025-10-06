import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Mail, Lock } from 'lucide-react';

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showRecovery, setShowRecovery] = useState(false);
  const [recoveryEmail, setRecoveryEmail] = useState('');
  const [recoveryLoading, setRecoveryLoading] = useState(false);
  const [recoveryMessage, setRecoveryMessage] = useState('');

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(formData.email, formData.password);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  const handleRecovery = async (e) => {
    e.preventDefault();
    setRecoveryLoading(true);
    setRecoveryMessage('');

    try {
      const response = await fetch('http://localhost:8000/auth/recuperar-contrasena', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: recoveryEmail }),
      });

      const data = await response.json();

      if (response.ok) {
        setRecoveryMessage('Se ha enviado un enlace de recuperación a tu email');
        setRecoveryEmail('');
        setShowRecovery(false);
      } else {
        setRecoveryMessage(data.detail || 'Error al enviar el enlace de recuperación');
      }
    } catch (err) {
      setRecoveryMessage('Error de conexión. Inténtalo de nuevo.');
    } finally {
      setRecoveryLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sistema de Notas
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Inicia sesión en tu cuenta
          </p>
        </div>
        
        {/* Formulario principal */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            {/* Campo email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className="w-full px-3 py-2 pl-10 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors border-gray-300 bg-white"
                  placeholder="tu@email.com"
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
            </div>

             {/* Campo contraseña */}
             <div>
               <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                 Contraseña
               </label>
               <div className="mt-1 flex items-center space-x-2">
                 <input
                   id="password"
                   name="password"
                   type={showPassword ? 'text' : 'password'}
                   autoComplete="current-password"
                   required
                   className={`flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors ${
                     showPassword 
                       ? 'border-green-300 bg-green-50' 
                       : 'border-gray-300 bg-white'
                   }`}
                   placeholder="Tu contraseña"
                   value={formData.password}
                   onChange={handleChange}
                 />
                 
                 {/* Botón para mostrar/ocultar contraseña - A la derecha */}
                 <button
                   type="button"
                   onClick={() => setShowPassword(!showPassword)}
                   title={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                   style={{ 
                     width: '40px',
                     height: '40px',
                     background: '#F3F4F6',
                     border: '1px solid #D1D5DB',
                     borderRadius: '8px',
                     cursor: 'pointer',
                     display: 'flex',
                     alignItems: 'center',
                     justifyContent: 'center',
                     fontSize: '20px'
                   }}
                   onMouseOver={(e) => e.target.style.background = '#E5E7EB'}
                   onMouseOut={(e) => e.target.style.background = '#F3F4F6'}
                 >
                   {showPassword ? '🙈' : '👁️'}
                 </button>
               </div>
             </div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {/* Botón de inicio de sesión */}
          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                'Iniciar Sesión'
              )}
            </button>
          </div>

          {/* Enlace recuperación */}
          <div className="text-center">
            <button
              type="button"
              onClick={() => setShowRecovery(!showRecovery)}
              style={{ 
                background: '#EFF6FF',
                border: '2px solid #3B82F6',
                borderRadius: '8px',
                cursor: 'pointer',
                padding: '12px 24px',
                fontSize: '14px',
                color: '#1E40AF',
                fontWeight: '600',
                margin: '16px 0'
              }}
              onMouseOver={(e) => {
                e.target.style.background = '#DBEAFE';
                e.target.style.borderColor = '#1D4ED8';
              }}
              onMouseOut={(e) => {
                e.target.style.background = '#EFF6FF';
                e.target.style.borderColor = '#3B82F6';
              }}
            >
              ¿Olvidaste tu contraseña?
            </button>
          </div>
        </form>

        {/* Panel recuperación */}
        {showRecovery && (
          <div className="mt-8 p-6 bg-white rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Recuperar Contraseña</h3>
            <p className="text-sm text-gray-600 mb-4">
              Ingresa tu email y te enviaremos un enlace para restablecer tu contraseña.
            </p>
            
            {recoveryMessage && (
              <div className={`mb-4 p-3 rounded-lg ${
                recoveryMessage.includes('enviado') 
                  ? 'bg-green-50 border border-green-200 text-green-600' 
                  : 'bg-red-50 border border-red-200 text-red-600'
              }`}>
                {recoveryMessage}
              </div>
            )}

            <form onSubmit={handleRecovery} className="space-y-4">
              <div>
                <label htmlFor="recoveryEmail" className="block text-sm font-medium text-gray-700">
                  Email
                </label>
                <div className="mt-1 relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="recoveryEmail"
                    type="email"
                    value={recoveryEmail}
                    onChange={(e) => setRecoveryEmail(e.target.value)}
                    required
                    className="w-full px-3 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="Tu email"
                  />
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  type="submit"
                  disabled={recoveryLoading}
                  className="flex-1 bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  {recoveryLoading ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mx-auto"></div>
                  ) : (
                    'Enviar Enlace'
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowRecovery(false);
                    setRecoveryMessage('');
                    setRecoveryEmail('');
                  }}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Usuarios de prueba */}
        <div className="mt-8 p-4 bg-gray-100 rounded-lg">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Usuarios de prueba:</h3>
          <div className="space-y-2 text-xs text-gray-600">
            <div><strong>Admin:</strong> admin@sistema.com / admin123</div>
            <div><strong>Docente:</strong> juan.docente@sistema.com / docente123</div>
            <div><strong>Alumno:</strong> carlos.alumno@sistema.com / alumno123</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

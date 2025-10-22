import React, { useState } from 'react';
import { chatService } from '../services/chatService';
import { useAuth } from '../contexts/AuthContext';

const ROLE_LABELS = {
  admin: 'Asistente Admin',
  docente: 'Asistente Docente',
  alumno: 'Asistente Alumno',
};

export default function ChatBot() {
  const { user } = useAuth();
  const role = user?.rol || 'alumno';

  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    const content = input.trim();
    if (!content) return;
    const newMessages = [...messages, { role: 'user', content }];
    setMessages(newMessages);
    setInput('');
    setLoading(true);
    try {
      const { reply } = await chatService.send(role, newMessages);
      setMessages([...newMessages, { role: 'assistant', content: reply }]);
    } catch (e) {
      // Mostrar detalle del backend si está disponible
      const detail = e?.response?.data?.detail || e?.message || 'Error desconocido';
      console.error('ChatBot error:', e);
      setMessages([...newMessages, { role: 'assistant', content: `Error al obtener respuesta: ${detail}` }]);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div>
      {/* Botón flotante */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-4 right-4 z-50 bg-indigo-600 text-white px-4 py-2 rounded-full shadow-lg hover:bg-indigo-700"
        title="Abrir asistente"
      >
        {open ? 'Cerrar Chat' : 'Chat'}
      </button>

      {/* Ventana de chat */}
      {open && (
        <div className="fixed bottom-20 right-4 z-50 w-96 bg-white border rounded-lg shadow-xl flex flex-col">
          <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
            <div className="font-semibold text-gray-800">{ROLE_LABELS[role] || 'Asistente'}</div>
            <button onClick={() => setOpen(false)} className="text-gray-500 hover:text-gray-700">✕</button>
          </div>

          <div className="p-3 h-80 overflow-y-auto space-y-3">
            {messages.length === 0 && (
              <div className="text-sm text-gray-500">Escribe tu pregunta para el sistema de notas.</div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`text-sm ${m.role === 'user' ? 'text-right' : 'text-left'}`}>
                <div className={`inline-block px-3 py-2 rounded-lg ${m.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
                  {m.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="text-xs text-gray-500">Pensando...</div>
            )}
          </div>

          <div className="p-3 border-t">
            <textarea
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Escribe tu mensaje y presiona Enter"
              className="w-full border rounded-md p-2 text-sm focus:outline-none focus:ring focus:border-indigo-500"
            />
            <div className="mt-2 flex justify-end">
              <button
                onClick={sendMessage}
                disabled={loading}
                className="bg-indigo-600 text-white px-3 py-1 rounded-md text-sm hover:bg-indigo-700 disabled:opacity-50"
              >
                Enviar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
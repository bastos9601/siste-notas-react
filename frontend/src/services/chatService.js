import api from './api';

export const chatService = {
  send: async (role, messages, options = {}) => {
    const payload = {
      messages,
      temperature: options.temperature ?? 0.2,
      model: options.model,
    };
    const { data } = await api.post(`/chat/${role}`, payload);
    return data; // { reply }
  },
};
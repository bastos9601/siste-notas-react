import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { adminService } from '../services/adminService';

const ThemeContext = createContext({
  isDark: false,
  setDark: () => {},
  toggleDark: () => {},
});

export const ThemeProvider = ({ children }) => {
  const [isDark, setIsDark] = useState(false);

  // Inicializar desde localStorage y configuración pública (si existe)
  useEffect(() => {
    const saved = localStorage.getItem('modo_oscuro');
    if (saved !== null) {
      setIsDark(saved === 'true');
    } else {
      // Fallback: usar configuración pública del backend
      adminService
        .getConfiguracionPublica()
        .then((cfg) => {
          if (typeof cfg?.modo_oscuro === 'boolean') {
            setIsDark(cfg.modo_oscuro);
          }
        })
        .catch(() => {});
    }
  }, []);

  // Aplicar la clase 'dark' al elemento html
  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('modo_oscuro', String(isDark));
  }, [isDark]);

  const value = useMemo(
    () => ({
      isDark,
      setDark: setIsDark,
      toggleDark: () => setIsDark((d) => !d),
    }),
    [isDark]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = () => useContext(ThemeContext);
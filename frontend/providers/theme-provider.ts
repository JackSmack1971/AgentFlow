'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

export type Theme = 'light' | 'dark';

export interface ThemeContextValue {
  theme: Theme;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>('light');

  useEffect(() => {
    try {
      const stored = localStorage.getItem('theme') as Theme | null;
      if (stored === 'dark' || stored === 'light') {
        setTheme(stored);
        document.documentElement.classList.toggle('dark', stored === 'dark');
      }
    } catch {
      /* ignore storage errors */
    }
  }, []);

  function toggle(): void {
    try {
      const next: Theme = theme === 'light' ? 'dark' : 'light';
      document.documentElement.classList.toggle('dark', next === 'dark');
      localStorage.setItem('theme', next);
      setTheme(next);
    } catch {
      /* ignore storage errors */
    }
  }

  const value: ThemeContextValue = { theme, toggle };
  return React.createElement(ThemeContext.Provider, { value }, children);
};

export const useTheme = (): ThemeContextValue => {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('ThemeContext not found');
  }
  return ctx;
};

export default ThemeProvider;

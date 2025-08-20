import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { ThemeProvider, useTheme } from './theme-provider.ts';

const storage: Record<string, string> = {};
(global as any).localStorage = {
  getItem: (k: string) => (k in storage ? storage[k] : null),
  setItem: (k: string, v: string) => {
    storage[k] = v;
  },
};
(global as any).document = { documentElement: { classList: { toggle: () => {} } } };

let saved: string | null = null;
function Test() {
  const { toggle } = useTheme();
  toggle();
  saved = localStorage.getItem('theme');
  return null;
}

renderToStaticMarkup(React.createElement(ThemeProvider, null, React.createElement(Test, null)));
assert.equal(saved, 'dark');

console.log('ThemeProvider tests passed');

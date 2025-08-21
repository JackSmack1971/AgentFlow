import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import MemoryPage from './page.tsx';

process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost';

(async () => {
  const html = renderToStaticMarkup(<MemoryPage />);
  assert.ok(html.includes('Dashboard'));
  assert.ok(html.includes('Memory'));
  console.log('MemoryPage tests passed');
})();

import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import AgentsPage from './page.tsx';

process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost';
(global as any).fetch = async () =>
  new Response(
    JSON.stringify([{ id: '1', name: 'A1' }]),
    { status: 200, headers: { 'Content-Type': 'application/json' } },
  );

(async () => {
  const html = renderToStaticMarkup(await AgentsPage());
  assert.ok(html.includes('A1'));
  assert.ok(html.includes('/agents/1/edit'));
  assert.ok(html.includes('/agents/1/test'));
  console.log('AgentsPage tests passed');
})();

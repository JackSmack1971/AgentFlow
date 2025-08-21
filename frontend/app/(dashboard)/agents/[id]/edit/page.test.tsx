import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import Page from './page.tsx';

process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost';
(global as any).fetch = async () =>
  new Response(
    JSON.stringify({ id: '1', name: 'Agent1' }),
    { status: 200, headers: { 'Content-Type': 'application/json' } },
  );

(async () => {
  const html = renderToStaticMarkup(await Page({ params: Promise.resolve({ id: '1' }) }));
  assert.ok(html.includes('value="Agent1"'));
  console.log('AgentEditPage tests passed');
})();

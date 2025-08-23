import assert from 'node:assert/strict';
import { renderToStaticMarkup } from 'react-dom/server';
import KnowledgePage from './page.tsx';

process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost';
globalThis.fetch = async () =>
  new Response(JSON.stringify([{ id: '1', title: 'Doc1' }]), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });

(async () => {
  const html = renderToStaticMarkup(await KnowledgePage());
  assert.ok(html.includes('Knowledge'));
  assert.ok(html.includes('Doc1'));
  console.log('KnowledgePage tests passed');
})();

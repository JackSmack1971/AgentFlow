process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost";

import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import RootLayout from './root-layout.ts';
import { useAuth, type AuthContextValue } from '../providers/auth-provider.ts';

const storage: Record<string, string> = {};
(global as any).localStorage = {
  getItem: (k: string) => (k in storage ? storage[k] : null),
  setItem: (k: string, v: string) => {
    storage[k] = v;
  },
  removeItem: (k: string) => {
    delete storage[k];
  },
};

(global as any).fetch = async () =>
  new Response(
    JSON.stringify({ access_token: 'access1', refresh_token: 'refresh1' }),
    { status: 200, headers: { 'Content-Type': 'application/json' } },
  );

async function testLayout() {
  let ctx: AuthContextValue | undefined;
  function Child() {
    ctx = useAuth();
    ctx.login({ email: 'a@b.com', password: 'x' });
    return React.createElement('div', null, 'child');
  }
  const html = renderToStaticMarkup(
    React.createElement(RootLayout, null, React.createElement(Child, null)),
  );
  assert.ok(html.includes('<nav'));
  await new Promise((r) => setTimeout(r, 0));
  assert.equal(storage.accessToken, 'access1');
}

(async () => {
  await testLayout();
  console.log('RootLayout tests passed');
})();

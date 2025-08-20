import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import AuthProvider, { useAuth } from './auth-provider.ts';
import type { AuthContextValue } from './auth-provider.ts';

// type check export
let _ctxType: AuthContextValue | null = null;
_ctxType = _ctxType;

process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost';

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

const responses: Record<string, any> = {
  '/auth/login': { access_token: 'access1', refresh_token: 'refresh1' },
  '/auth/refresh': { access_token: 'access2', refresh_token: 'refresh2' },
  '/auth/logout': { status: 'ok' },
};

(global as any).fetch = async (url: string, init?: RequestInit) => {
  const path = url.replace(/^.*\/auth/, '/auth');
  const body = responses[path];
  return new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });
};

async function testContextMethods() {
  let ctx: AuthContextValue | undefined;
  function Test() {
    ctx = useAuth();
    return null;
  }
  renderToStaticMarkup(
    React.createElement(AuthProvider, null, React.createElement(Test, null)),
  );
  assert.ok(ctx?.login);
  assert.ok(ctx?.logout);
  assert.ok(ctx?.refresh);
}

async function testTokenStorage() {
  let ctx: AuthContextValue | undefined;
  function Test() {
    ctx = useAuth();
    ctx.login({ email: 'a@b.com', password: 'x' });
    return null;
  }
  renderToStaticMarkup(
    React.createElement(AuthProvider, null, React.createElement(Test, null)),
  );
  await new Promise((r) => setTimeout(r, 0));
  assert.equal(storage.accessToken, 'access1');
  assert.equal(storage.refreshToken, 'refresh1');
  await ctx!.logout();
  assert.equal(storage.accessToken, undefined);
  assert.equal(storage.refreshToken, undefined);
}

(async () => {
  await testContextMethods();
  await testTokenStorage();
  console.log('All tests passed');
})();

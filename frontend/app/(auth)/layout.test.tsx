import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import AuthLayout from './layout.tsx';

async function run(): Promise<void> {
  process.env.NEXT_PUBLIC_BRAND_NAME = 'AgentFlow';
  const html = renderToStaticMarkup(
    <AuthLayout>
      <div>child</div>
    </AuthLayout>,
  );
  assert.ok(html.includes('AgentFlow'));
  assert.ok(html.includes('child'));

  delete process.env.NEXT_PUBLIC_BRAND_NAME;
  const html2 = renderToStaticMarkup(
    <AuthLayout>
      <div>child</div>
    </AuthLayout>,
  );
  assert.ok(!html2.includes('AgentFlow'));
}

run().then(() => console.log('AuthLayout tests passed'));

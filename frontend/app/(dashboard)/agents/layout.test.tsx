import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import AgentsLayout from './layout.tsx';

const html = renderToStaticMarkup(
  <AgentsLayout>
    <div>child</div>
  </AgentsLayout>,
);
assert.ok(html.includes('Dashboard'));
assert.ok(html.includes('Agents'));
assert.ok(html.includes('child'));
console.log('AgentsLayout tests passed');

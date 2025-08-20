import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { ErrorBoundary } from './error-boundary.ts';

const boundary = new ErrorBoundary({
  children: React.createElement('div', null, 'ok'),
  fallback: React.createElement('div', null, 'failed'),
});
boundary.state = { hasError: true } as any;
const html = renderToStaticMarkup(boundary.render() as React.ReactElement);
assert.ok(html.includes('failed'));

console.log('ErrorBoundary tests passed');

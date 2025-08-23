import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import Main from './main.tsx';

const html = renderToStaticMarkup(
  React.createElement(Main, null, React.createElement('div', null, 'content')),
);
assert.ok(html.includes('<main'));
assert.ok(html.includes('content'));

console.log('Main tests passed');

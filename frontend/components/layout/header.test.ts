import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import Header from './header.tsx';

const html = renderToStaticMarkup(React.createElement(Header));
assert.ok(html.includes('<header'));
assert.ok(html.includes('md:hidden'));

console.log('Header tests passed');

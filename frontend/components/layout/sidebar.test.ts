import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import Sidebar from './sidebar.tsx';

const html = renderToStaticMarkup(React.createElement(Sidebar));
assert.ok(html.includes('<aside'));
assert.ok(html.includes('hidden md:block'));

console.log('Sidebar tests passed');

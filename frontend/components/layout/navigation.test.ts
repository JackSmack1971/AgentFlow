import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import Navigation from './navigation.ts';

const html = renderToStaticMarkup(React.createElement(Navigation));
assert.ok(html.includes('Home'));
assert.ok(html.includes('Dashboard'));
assert.ok(html.includes('md:flex'));
assert.ok(html.includes('md:hidden'));

console.log('Navigation tests passed');

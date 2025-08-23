import assert from 'node:assert/strict';
import { renderToStaticMarkup } from 'react-dom/server';
import DashboardPage from './page.tsx';

const html = renderToStaticMarkup(DashboardPage());
assert.ok(html.includes('Dashboard Overview'));
assert.ok(html.includes('/agents'));
assert.ok(html.includes('/knowledge'));
console.log('DashboardPage tests passed');

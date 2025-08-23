import React, { type ReactNode } from 'react';
import { AuthProvider } from '../providers/auth-provider.ts';
import { ThemeProvider } from '../providers/theme-provider.ts';
import Header from '../components/layout/header.tsx';
import Sidebar from '../components/layout/sidebar.tsx';
import Main from '../components/layout/main.tsx';
import { ErrorBoundary } from '../components/layout/error-boundary.ts';

export default function RootLayout({ children }: { children: ReactNode }): JSX.Element {
  return React.createElement(
    'html',
    { lang: 'en' },
    React.createElement(
      'body',
      { className: 'md:grid md:grid-cols-[sidebar_16rem_main_1fr]' },
      React.createElement(
        ErrorBoundary,
        null,
        React.createElement(
          ThemeProvider,
          null,
          React.createElement(
            AuthProvider,
            null,
            React.createElement(Header, null),
            React.createElement(Sidebar, null),
            React.createElement(Main, null, children),
          ),
        ),
      ),
    ),
  );
}

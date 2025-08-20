import React, { type ReactNode } from 'react';
import { AuthProvider } from '../providers/auth-provider.ts';
import { ThemeProvider } from '../providers/theme-provider.ts';
import Navigation from '../components/layout/navigation.ts';
import { ErrorBoundary } from '../components/layout/error-boundary.ts';

export default function RootLayout({ children }: { children: ReactNode }): JSX.Element {
  return React.createElement(
    'html',
    { lang: 'en' },
    React.createElement(
      'body',
      null,
      React.createElement(
        ErrorBoundary,
        null,
        React.createElement(
          ThemeProvider,
          null,
          React.createElement(
            AuthProvider,
            null,
            React.createElement(Navigation, null),
            children,
          ),
        ),
      ),
    ),
  );
}

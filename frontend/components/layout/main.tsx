import React, { type ReactNode } from 'react';

interface MainProps {
  children: ReactNode;
}

export default function Main({ children }: MainProps): JSX.Element {
  return React.createElement('main', { className: 'p-4' }, children);
}

export type { MainProps };

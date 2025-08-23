import React, { type ReactNode } from 'react';
import Navigation from './navigation.ts';

interface HeaderProps {
  children?: ReactNode;
}

export default function Header({ children }: HeaderProps): JSX.Element {
  return React.createElement(
    'header',
    { className: 'md:hidden border-b' },
    React.createElement(Navigation, null),
    children,
  );
}

export type { HeaderProps };

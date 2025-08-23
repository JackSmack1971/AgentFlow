import React, { type ReactNode } from 'react';
import Link from 'next/link.js';

interface SidebarItem {
  href: string;
  label: string;
}

interface SidebarProps {
  items?: SidebarItem[];
  children?: ReactNode;
}

const DEFAULT_ITEMS: SidebarItem[] = [
  { href: '/', label: 'Home' },
  { href: '/dashboard', label: 'Dashboard' },
];

export default function Sidebar({ items = DEFAULT_ITEMS, children }: SidebarProps): JSX.Element {
  const list = items.map((item) =>
    React.createElement(
      'li',
      { key: item.href, className: 'p-2' },
      React.createElement(Link, { href: item.href }, item.label),
    ),
  );
  return React.createElement(
    'aside',
    { className: 'hidden md:block w-64 border-r p-4' },
    React.createElement('ul', { className: 'space-y-2' }, ...list),
    children,
  );
}

export type { SidebarProps, SidebarItem };

'use client';

import React, { useState } from 'react';
import Link from 'next/link.js';

interface NavItem {
  href: string;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/', label: 'Home' },
  { href: '/dashboard', label: 'Dashboard' },
];

export default function Navigation(): JSX.Element {
  const [open, setOpen] = useState(false);
  function handleToggle(): void {
    setOpen((v) => !v);
  }
  const list = NAV_ITEMS.map((item) =>
    React.createElement(
      'li',
      { key: item.href, className: 'p-2' },
      React.createElement(Link, { href: item.href }, item.label),
    ),
  );
  return React.createElement(
    'nav',
    { className: 'border-b' },
    React.createElement(
      'div',
      { className: 'flex items-center justify-between p-4' },
      React.createElement(
        'button',
        {
          type: 'button',
          'aria-label': 'Toggle navigation',
          onClick: handleToggle,
          className: 'md:hidden',
        },
        '☰',
      ),
      React.createElement(
        'ul',
        { className: `${open ? 'block' : 'hidden'} md:flex md:gap-4` },
        ...list,
      ),
    ),
  );
}

import React, { type ReactNode } from 'react';
import Link from 'next/link.js';
import Navigation from '../../../components/layout/navigation.ts';

interface MemoryLayoutProps {
  children: ReactNode;
}

export default function MemoryLayout({ children }: MemoryLayoutProps): JSX.Element {
  return (
    <div>
      <Navigation />
      <nav aria-label="Breadcrumb" className="border-b p-4 text-sm">
        <ol className="flex gap-2">
          <li>
            <Link href="/dashboard">Dashboard</Link>
          </li>
          <li>/</li>
          <li>Memory</li>
        </ol>
      </nav>
      <div className="p-4">{children}</div>
    </div>
  );
}

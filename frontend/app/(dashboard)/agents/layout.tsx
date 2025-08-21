import React, { type ReactNode } from 'react';
import Link from 'next/link.js';
import Navigation from '../../../components/layout/navigation.ts';

interface AgentsLayoutProps {
  children: ReactNode;
}

export default function AgentsLayout({ children }: AgentsLayoutProps): JSX.Element {
  return (
    <div>
      <Navigation />
      <nav aria-label="Breadcrumb" className="border-b p-4 text-sm">
        <ol className="flex gap-2">
          <li>
            <Link href="/dashboard">Dashboard</Link>
          </li>
          <li>/</li>
          <li>Agents</li>
        </ol>
      </nav>
      <div className="p-4">{children}</div>
    </div>
  );
}

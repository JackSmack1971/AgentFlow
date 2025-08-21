import React from 'react';
import Link from 'next/link.js';
import MemoryBrowser from '../../../components/memory/memory-browser.tsx';

export default function MemoryPage(): JSX.Element {
  return (
    <div className="space-y-4">
      <nav aria-label="Breadcrumb" className="text-sm">
        <ol className="flex gap-2">
          <li>
            <Link href="/dashboard">Dashboard</Link>
          </li>
          <li>/</li>
          <li>Memory</li>
        </ol>
      </nav>
      <MemoryBrowser />
    </div>
  );
}

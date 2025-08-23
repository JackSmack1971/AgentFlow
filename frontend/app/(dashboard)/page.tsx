import Link from 'next/link.js';
// biome-ignore lint/correctness/noUnusedImports: React import required for JSX
import React from 'react';

export default function DashboardPage(): JSX.Element {
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-xl font-semibold">Dashboard Overview</h1>
      <ul className="space-y-2">
        <li>
          <Link href="/agents" className="text-blue-600">
            Agents
          </Link>
        </li>
        <li>
          <Link href="/knowledge" className="text-blue-600">
            Knowledge
          </Link>
        </li>
      </ul>
    </div>
  );
}

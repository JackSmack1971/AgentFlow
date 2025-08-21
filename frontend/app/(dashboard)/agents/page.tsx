import React from 'react';
import Link from 'next/link.js';
import ApiClient from '../../../lib/api.ts';
import type { Agent } from '../../../lib/types.ts';

class AgentsPageError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AgentsPageError';
  }
}

export default async function AgentsPage(): Promise<JSX.Element> {
  const client = new ApiClient();
  let agents: Agent[] = [];
  try {
    agents = await client.listAgents();
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error(new AgentsPageError(message));
  }
  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Agents</h1>
        <Link href="/agents/create" className="text-blue-600">
          Create Agent
        </Link>
      </div>
      <ul className="space-y-2">
        {agents.map((a) => (
          <li key={a.id} className="flex gap-4">
            <Link href={`/agents/${a.id}/edit`}>{a.name}</Link>
            <Link href={`/agents/${a.id}/test`} className="text-blue-600">
              Test
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

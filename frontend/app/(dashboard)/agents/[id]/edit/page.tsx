import React from 'react';
import ApiClient from '../../../../../lib/api.ts';
import type { Agent } from '../../../../../lib/types.ts';
import AgentForm from './form.tsx';

class AgentEditPageError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AgentEditPageError';
  }
}

async function fetchAgent(id: string): Promise<Agent | null> {
  const client = new ApiClient();
  try {
    return await client.getAgent(id, { timeoutMs: 5000, retries: 3 });
  } catch (error) {
    const msg = error instanceof Error ? error.message : 'Unknown error';
    console.error(new AgentEditPageError(msg));
    return null;
  }
}

export default async function AgentEditPage({ params }: { params: Promise<{ id: string }> }): Promise<JSX.Element> {
  const { id } = await params;
  const agent = await fetchAgent(id);
  if (!agent) {
    return <div>Failed to load agent.</div>;
  }
  return <AgentForm agent={agent} />;
}

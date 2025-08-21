'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import ApiClient from '../../../../../lib/api.ts';
import type { Agent, AgentUpdate } from '../../../../../lib/types.ts';

class AgentUpdateError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AgentUpdateError';
  }
}

export default function AgentForm({ agent }: { agent: Agent }): JSX.Element {
  const schema = z.object({ name: z.string().min(1, 'Name is required') });
  const client = new ApiClient();
  const [error, setError] = React.useState<string | null>(null);
  const { register, handleSubmit, formState: { errors } } = useForm<AgentUpdate>({
    resolver: zodResolver(schema),
    defaultValues: { name: agent.name },
  });
  const onSubmit = async (values: AgentUpdate): Promise<void> => {
    try {
      await client.updateAgent(agent.id, values, { timeoutMs: 5000, retries: 3 });
      setError(null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(new AgentUpdateError(msg).message);
    }
  };
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" aria-describedby={error ? 'form-error' : undefined}>
      <label htmlFor="name" className="block font-medium">Name</label>
      <input
        id="name"
        defaultValue={agent.name}
        {...register('name')}
        aria-invalid={Boolean(errors.name)}
        aria-describedby={errors.name ? 'name-error' : undefined}
        className="w-full border p-2"
      />
      {errors.name && <div id="name-error" role="alert" aria-live="assertive" className="text-red-600">{errors.name.message}</div>}
      {error && <div id="form-error" role="alert" aria-live="assertive" className="text-red-600">{error}</div>}
      <button type="submit" className="border px-4 py-2">Save</button>
    </form>
  );
}

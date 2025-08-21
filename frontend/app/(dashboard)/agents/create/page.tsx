'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Mirror of AgentPrompt schema in apps/api/app/models/schemas.py
interface AgentPrompt {
  prompt: string;
}

class AgentRunError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AgentRunError';
  }
}

const schema = z.object({ prompt: z.string().min(1, 'Prompt is required') });

async function postAgentPrompt(
  data: AgentPrompt,
  { timeoutMs = 5000, retries = 3 }: { timeoutMs?: number; retries?: number } = {},
): Promise<unknown> {
  for (let attempt = 0; attempt < retries; attempt++) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/agents/run`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
          signal: controller.signal,
        },
      );
      clearTimeout(timeout);
      if (!res.ok) {
        throw new AgentRunError(`Status ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      clearTimeout(timeout);
      if (attempt === retries - 1) {
        const msg = err instanceof Error ? err.message : 'Unknown error';
        throw new AgentRunError(msg);
      }
    }
  }
  throw new AgentRunError('Failed after retries');
}

export default function AgentRunPage(): JSX.Element {
  const [error, setError] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors } } = useForm<AgentPrompt>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: AgentPrompt): Promise<void> => {
    try {
      await postAgentPrompt(values);
      setError(null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(msg);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" aria-describedby={error ? 'form-error' : undefined}>
      <label htmlFor="prompt" className="block font-medium">Prompt</label>
      <textarea
        id="prompt"
        {...register('prompt')}
        aria-invalid={Boolean(errors.prompt)}
        aria-describedby={errors.prompt ? 'prompt-error' : undefined}
        className="w-full border p-2"
      />
      {errors.prompt && (
        <div id="prompt-error" role="alert" aria-live="assertive" className="text-red-600">
          {errors.prompt.message}
        </div>
      )}
      {error && (
        <div id="form-error" role="alert" aria-live="assertive" className="text-red-600">
          {error}
        </div>
      )}
      <button type="submit" className="border px-4 py-2">Run</button>
    </form>
  );
}


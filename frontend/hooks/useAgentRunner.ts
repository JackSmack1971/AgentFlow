import { useCallback } from 'react';
import { z } from 'zod';

class AgentRunnerError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AgentRunnerError';
  }
}

const promptSchema = z.object({ prompt: z.string().min(1) });

interface RunOpts {
  timeoutMs?: number;
  retries?: number;
  onChunk?: (chunk: string) => void;
}

async function readResponse(res: Response, onChunk?: (chunk: string) => void) {
  const reader = res.body!.getReader();
  let result = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    const chunk = new TextDecoder().decode(value);
    result += chunk;
    onChunk?.(chunk);
  }
  return result;
}

export function useAgentRunner(baseUrl: string = process.env.NEXT_PUBLIC_API_BASE_URL || '') {
  if (!baseUrl) throw new AgentRunnerError('API base URL not configured');
  const run = useCallback(
    async (prompt: string, opts: RunOpts = {}): Promise<string> => {
      const { timeoutMs = 5000, retries = 3, onChunk } = opts;
      const data = promptSchema.parse({ prompt });
      for (let attempt = 0; attempt < retries; attempt++) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), timeoutMs);
        try {
          const res = await fetch(`${baseUrl}/agents/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
            signal: controller.signal,
          });
          clearTimeout(timeout);
          if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
          return await readResponse(res, onChunk);
        } catch (error) {
          clearTimeout(timeout);
          if (attempt === retries - 1) {
            const msg = error instanceof Error ? error.message : 'Unknown error';
            throw new AgentRunnerError(msg);
          }
        }
      }
      throw new AgentRunnerError('Exceeded retry attempts');
    },
    [baseUrl],
  );
  return { run };
}

export default useAgentRunner;

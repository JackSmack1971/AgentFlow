import type { MemoryItem, RagQuery, AgentPrompt } from './types.ts';
import { z } from 'zod';

class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

const memoryItemSchema = z.object({
  id: z.string().optional(),
  text: z.string().min(1),
  scope: z.enum(['user', 'agent', 'session', 'global']).optional(),
  userId: z.string().optional(),
  agentId: z.string().optional(),
  runId: z.string().optional(),
  metadata: z.record(z.unknown()).nullable().optional(),
});

const ragQuerySchema = z.object({
  query: z.string().min(1),
  useKg: z.boolean().optional(),
  limit: z.number().int().positive().optional(),
});

const agentPromptSchema = z.object({
  prompt: z.string().min(1),
});

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_BASE_URL || '') {
    if (!baseUrl) {
      throw new ApiError('API base URL not configured');
    }
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, init: RequestInit & { timeoutMs?: number; retries?: number } = {}): Promise<T> {
    const { timeoutMs = 5000, retries = 3, ...options } = init;
    for (let attempt = 0; attempt < retries; attempt++) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const res = await fetch(`${this.baseUrl}${endpoint}`, { ...options, signal: controller.signal });
        clearTimeout(timeout);
        if (!res.ok) {
          throw new ApiError(`Request failed with status ${res.status}`, res.status);
        }
        return (await res.json()) as T;
      } catch (error) {
        clearTimeout(timeout);
        if (attempt === retries - 1) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new ApiError(message);
        }
      }
    }
    throw new ApiError('Exceeded retry attempts');
  }

  /**
   * Create a memory item.
   */
  async createMemoryItem(item: MemoryItem): Promise<MemoryItem> {
    const data = memoryItemSchema.parse(item);
    try {
      return await this.request<MemoryItem>('/memory/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError((error as Error).message);
    }
  }

  /**
   * Run a RAG query.
   */
  async runRag(query: RagQuery): Promise<unknown> {
    const data = ragQuerySchema.parse(query);
    try {
      return await this.request<unknown>('/rag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError((error as Error).message);
    }
  }

  /**
   * Run an agent prompt.
   */
  async runAgentPrompt(prompt: AgentPrompt): Promise<{ result: unknown }> {
    const data = agentPromptSchema.parse(prompt);
    try {
      return await this.request<{ result: unknown }>('/agents/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError((error as Error).message);
    }
  }
}

export default ApiClient;

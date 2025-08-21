import type { MemoryItem, RAGQuery, AgentPrompt, Agent, AgentUpdate } from './types.ts';
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
  sessionId: z.string().optional(),
  tags: z.array(z.string()).optional(),
  metadata: z.record(z.unknown()).optional(),
  ttl: z.number().int().positive().optional(),
  createdAt: z.string().optional(),
  expiresAt: z.string().nullable().optional(),
});
const memoryItemsSchema = z.array(memoryItemSchema);
const memoryItemUpdateSchema = z.object({
  text: z.string().min(1).optional(),
  tags: z.array(z.string()).optional(),
  metadata: z.record(z.unknown()).optional(),
  ttl: z.number().int().positive().optional(),
});
const listParamsSchema = z.object({
  offset: z.number().int().min(0).optional(),
  limit: z.number().int().min(1).max(100).optional(),
  scope: z.enum(['user', 'agent', 'session', 'global']).optional(),
  tags: z.array(z.string()).optional(),
});
const searchParamsSchema = listParamsSchema.extend({ q: z.string().min(1) });

const ragQuerySchema = z.object({
  query: z.string().min(1),
  useKg: z.boolean().optional(),
  limit: z.number().int().positive().optional(),
});

const agentPromptSchema = z.object({
  prompt: z.string().min(1),
});

const agentSchema = z.object({ id: z.string(), name: z.string() });
const agentsSchema = z.array(agentSchema);
const agentUpdateSchema = z.object({ name: z.string().min(1) });

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
        if (res.status === 204) {
          return undefined as T;
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

  async listMemoryItems(
    params: z.infer<typeof listParamsSchema> = {},
  ): Promise<MemoryItem[]> {
    const query = listParamsSchema.parse(params);
    const qs = new URLSearchParams();
    if (query.offset !== undefined) qs.set('offset', String(query.offset));
    if (query.limit !== undefined) qs.set('limit', String(query.limit));
    if (query.scope) qs.set('scope', query.scope);
    if (query.tags) query.tags.forEach((t) => qs.append('tags', t));
    try {
      const data = await this.request<unknown>(`/memory/items?${qs.toString()}`);
      return memoryItemsSchema.parse(data);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError((error as Error).message);
    }
  }

  async searchMemoryItems(
    params: z.infer<typeof searchParamsSchema>,
  ): Promise<MemoryItem[]> {
    const query = searchParamsSchema.parse(params);
    const qs = new URLSearchParams({ q: query.q });
    if (query.offset !== undefined) qs.set('offset', String(query.offset));
    if (query.limit !== undefined) qs.set('limit', String(query.limit));
    if (query.scope) qs.set('scope', query.scope);
    if (query.tags) query.tags.forEach((t) => qs.append('tags', t));
    try {
      const data = await this.request<unknown>(`/memory/search?${qs.toString()}`);
      return memoryItemsSchema.parse(data);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError((error as Error).message);
    }
  }

  async updateMemoryItem(
    id: string,
    updates: z.infer<typeof memoryItemUpdateSchema>,
  ): Promise<MemoryItem> {
    const data = memoryItemUpdateSchema.parse(updates);
    try {
      const res = await this.request<unknown>(`/memory/items/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      return memoryItemSchema.parse(res);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError((error as Error).message);
    }
  }

  async deleteMemoryItem(id: string): Promise<void> {
    try {
      await this.request(`/memory/items/${id}`, { method: 'DELETE' });
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
  async runRag(query: RAGQuery): Promise<unknown> {
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

  async listAgents(): Promise<Agent[]> {
    try {
      const data = await this.request<unknown>('/agents');
      return agentsSchema.parse(data);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError((error as Error).message);
    }
  }

  async getAgent(id: string, init: { timeoutMs?: number; retries?: number } = {}): Promise<Agent> {
    try {
      const data = await this.request<unknown>(`/agents/${id}`, init);
      return agentSchema.parse(data);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError((error as Error).message);
    }
  }

  async updateAgent(
    id: string,
    updates: AgentUpdate,
    init: { timeoutMs?: number; retries?: number } = {},
  ): Promise<Agent> {
    const data = agentUpdateSchema.parse(updates);
    try {
      const res = await this.request<unknown>(`/agents/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        ...init,
      });
      return agentSchema.parse(res);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError((error as Error).message);
    }
  }
}

export default ApiClient;

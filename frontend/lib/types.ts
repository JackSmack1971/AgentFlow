export type MemoryScope = "user" | "agent" | "session" | "global";

export interface MemoryItem {
  id?: string;
  text: string;
  scope?: MemoryScope;
  userId?: string;
  agentId?: string;
  sessionId?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
  ttl?: number;
  createdAt?: string;
  expiresAt?: string | null;
}

export interface RAGQuery {
  query: string;
  useKg?: boolean;
  limit?: number;
}

export interface AgentPrompt {
  prompt: string;
}

export interface Agent {
  id: string;
  name: string;
}

export interface AgentUpdate {
  name: string;
}

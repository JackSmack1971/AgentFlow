export interface MemoryItem {
  id?: string;
  text: string;
  scope?: "user" | "agent" | "session" | "global";
  userId?: string;
  agentId?: string;
  runId?: string;
  metadata?: Record<string, unknown> | null;
}

export interface RagQuery {
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

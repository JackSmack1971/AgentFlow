# AGENTS.md: Frontend Utilities Guidelines

This document provides specific guidance for AI models working with frontend utilities in `/frontend/lib/`. These guidelines are derived from the TypeScript 5.x, React 18, and API client rulesets.

## 1. Project Scope & Architecture
*   **Primary Purpose:** Frontend utility functions, API clients, type definitions, and helper functions
*   **Core Technologies:** TypeScript 5.x, Zod validation, custom hooks, API integration patterns
*   **Architecture Pattern:** Modular utilities with clear separation of concerns and strong type safety

## 2. Library Organization Standards

### File Structure Requirements
*   **MANDATORY:** Organize utilities by functional domain:
    ```
    lib/
    ├── api/                     # API client and integration
    │   ├── client.ts           # Base API client
    │   ├── agents.ts           # Agent API endpoints
    │   ├── memory.ts           # Memory API endpoints
    │   ├── auth.ts             # Authentication API
    │   └── types.ts            # API response types
    ├── hooks/                   # Custom React hooks
    │   ├── use-agents.ts
    │   ├── use-memory.ts
    │   └── use-auth.ts
    ├── utils/                   # General utilities
    │   ├── format.ts           # Formatting functions
    │   ├── validation.ts       # Validation helpers
    │   ├── date.ts             # Date utilities
    │   └── storage.ts          # Client storage helpers
    ├── types/                   # Type definitions
    │   ├── api.ts              # API types
    │   ├── agent.ts            # Agent domain types
    │   └── common.ts           # Shared types
    ├── constants.ts             # Application constants
    ├── config.ts               # Configuration
    └── index.ts                # Main exports
    ```

### Export Patterns
*   **REQUIRED:** Use barrel exports for clean imports
*   **MANDATORY:** Export types and runtime values separately when needed
*   **CRITICAL:** Maintain clear public API boundaries
*   **REQUIRED:** Document exported functions with JSDoc

## 3. TypeScript Utility Standards [Hard Constraint]

### Type-First Development
*   **CRITICAL:** Define comprehensive TypeScript types for all utilities
*   **MANDATORY:** Use strict TypeScript configuration
*   **REQUIRED:** Implement runtime validation with Zod where appropriate
*   **CRITICAL:** Never use `any` type without explicit justification

```typescript
// types/api.ts - API response types
export interface ApiResponse<T = unknown> {
  data: T;
  message: string;
  success: boolean;
}

export interface ApiError {
  error: string;
  message: string;
  code: string;
  details?: Record<string, unknown>;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// Result type for error handling
export type Result<T, E = ApiError> = 
  | { success: true; data: T }
  | { success: false; error: E };

// Generic API endpoint function type
export type ApiEndpoint<TRequest = void, TResponse = unknown> = 
  TRequest extends void 
    ? () => Promise<Result<TResponse>>
    : (request: TRequest) => Promise<Result<TResponse>>;
```

### Utility Function Types
*   **REQUIRED:** Use function overloads for flexible utility functions
*   **MANDATORY:** Implement proper generic constraints
*   **CRITICAL:** Provide comprehensive type guards
*   **REQUIRED:** Use branded types for domain-specific values

```typescript
// utils/validation.ts
import { z } from 'zod';

// Type guards
export function isString(value: unknown): value is string {
  return typeof value === 'string';
}

export function isNotNull<T>(value: T | null): value is T {
  return value !== null;
}

export function isNotUndefined<T>(value: T | undefined): value is T {
  return value !== undefined;
}

// Generic validation with Zod
export function validateData<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): Result<T, { message: string; issues: z.ZodIssue[] }> {
  try {
    const validatedData = schema.parse(data);
    return { success: true, data: validatedData };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        success: false,
        error: {
          message: 'Validation failed',
          issues: error.issues
        }
      };
    }
    return {
      success: false,
      error: {
        message: 'Unknown validation error',
        issues: []
      }
    };
  }
}

// Branded types for domain values
export type AgentId = string & { readonly __brand: 'AgentId' };
export type UserId = string & { readonly __brand: 'UserId' };

export function createAgentId(id: string): AgentId {
  // Validate ID format
  if (!/^[a-zA-Z0-9-_]+$/.test(id)) {
    throw new Error('Invalid agent ID format');
  }
  return id as AgentId;
}
```

## 4. API Client Implementation

### Base API Client
*   **REQUIRED:** Implement type-safe API client with error handling
*   **MANDATORY:** Use consistent request/response patterns
*   **CRITICAL:** Handle authentication and token refresh
*   **REQUIRED:** Implement proper retry logic and timeouts

```typescript
// api/client.ts
interface ApiClientConfig {
  baseUrl: string;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
}

class ApiClient {
  private baseUrl: string;
  private timeout: number;
  private retryAttempts: number;
  private retryDelay: number;
  private authToken: string | null = null;

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl;
    this.timeout = config.timeout ?? 30000;
    this.retryAttempts = config.retryAttempts ?? 3;
    this.retryDelay = config.retryDelay ?? 1000;
  }

  setAuthToken(token: string): void {
    this.authToken = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Result<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.authToken) {
      headers.Authorization = `Bearer ${this.authToken}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await this.retryRequest(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          success: false,
          error: {
            error: 'HTTP_ERROR',
            message: `Request failed with status ${response.status}`,
            code: response.status.toString(),
            details: errorData,
          },
        };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error) {
        return {
          success: false,
          error: {
            error: 'NETWORK_ERROR',
            message: error.message,
            code: 'FETCH_ERROR',
          },
        };
      }

      return {
        success: false,
        error: {
          error: 'UNKNOWN_ERROR',
          message: 'An unknown error occurred',
          code: 'UNKNOWN',
        },
      };
    }
  }

  private async retryRequest(
    url: string,
    options: RequestInit,
    attempt = 1
  ): Promise<Response> {
    try {
      return await fetch(url, options);
    } catch (error) {
      if (attempt >= this.retryAttempts) {
        throw error;
      }

      await new Promise(resolve => 
        setTimeout(resolve, this.retryDelay * Math.pow(2, attempt - 1))
      );

      return this.retryRequest(url, options, attempt + 1);
    }
  }

  async get<T>(endpoint: string): Promise<Result<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T, D = unknown>(
    endpoint: string,
    data?: D
  ): Promise<Result<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T, D = unknown>(
    endpoint: string,
    data: D
  ): Promise<Result<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<Result<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

// Singleton instance
export const apiClient = new ApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  retryAttempts: 3,
});

export default apiClient;
```

### Domain-Specific API Clients
*   **REQUIRED:** Create domain-specific API modules
*   **MANDATORY:** Use consistent parameter and response types
*   **CRITICAL:** Implement proper error handling for domain operations
*   **REQUIRED:** Provide JSDoc documentation for all API functions

```typescript
// api/agents.ts
import { z } from 'zod';
import apiClient from './client';
import { AgentId, UserId } from '../types/common';

// Zod schemas for validation
const agentSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  status: z.enum(['active', 'inactive', 'training', 'error']),
  modelProvider: z.enum(['openai', 'anthropic', 'google', 'local']),
  temperature: z.number(),
  maxTokens: z.number(),
  createdAt: z.string().transform(val => new Date(val)),
  updatedAt: z.string().transform(val => new Date(val)),
  ownerId: z.string(),
  runCount: z.number(),
});

const agentCreateSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  model: z.string(),
  temperature: z.number().min(0).max(2),
  maxTokens: z.number().min(1).max(32000),
  systemPrompt: z.string().max(2000).optional(),
});

const agentUpdateSchema = agentCreateSchema.partial();

export type Agent = z.infer<typeof agentSchema>;
export type AgentCreate = z.infer<typeof agentCreateSchema>;
export type AgentUpdate = z.infer<typeof agentUpdateSchema>;

export interface AgentListParams {
  skip?: number;
  limit?: number;
  search?: string;
  status?: Agent['status'];
  sortBy?: 'name' | 'createdAt' | 'updatedAt';
  sortOrder?: 'asc' | 'desc';
}

/**
 * Fetch list of agents with optional filtering and pagination
 */
export async function listAgents(
  params: AgentListParams = {}
): Promise<Result<Agent[]>> {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) {
      searchParams.append(key, String(value));
    }
  });

  const endpoint = `/agents${searchParams.toString() ? `?${searchParams}` : ''}`;
  const result = await apiClient.get<Agent[]>(endpoint);

  if (result.success) {
    // Validate response data
    const validation = z.array(agentSchema).safeParse(result.data);
    if (!validation.success) {
      return {
        success: false,
        error: {
          error: 'VALIDATION_ERROR',
          message: 'Invalid agent data received',
          code: 'SCHEMA_MISMATCH',
        },
      };
    }
    return { success: true, data: validation.data };
  }

  return result;
}

/**
 * Get a specific agent by ID
 */
export async function getAgent(id: AgentId): Promise<Result<Agent>> {
  const result = await apiClient.get<Agent>(`/agents/${id}`);
  
  if (result.success) {
    const validation = agentSchema.safeParse(result.data);
    if (!validation.success) {
      return {
        success: false,
        error: {
          error: 'VALIDATION_ERROR',
          message: 'Invalid agent data received',
          code: 'SCHEMA_MISMATCH',
        },
      };
    }
    return { success: true, data: validation.data };
  }

  return result;
}

/**
 * Create a new agent
 */
export async function createAgent(
  data: AgentCreate
): Promise<Result<Agent>> {
  // Validate input
  const validation = agentCreateSchema.safeParse(data);
  if (!validation.success) {
    return {
      success: false,
      error: {
        error: 'VALIDATION_ERROR',
        message: 'Invalid agent creation data',
        code: 'INPUT_VALIDATION',
        details: { issues: validation.error.issues },
      },
    };
  }

  return apiClient.post<Agent, AgentCreate>('/agents', validation.data);
}

/**
 * Update an existing agent
 */
export async function updateAgent(
  id: AgentId,
  data: AgentUpdate
): Promise<Result<Agent>> {
  const validation = agentUpdateSchema.safeParse(data);
  if (!validation.success) {
    return {
      success: false,
      error: {
        error: 'VALIDATION_ERROR',
        message: 'Invalid agent update data',
        code: 'INPUT_VALIDATION',
        details: { issues: validation.error.issues },
      },
    };
  }

  return apiClient.put<Agent, AgentUpdate>(`/agents/${id}`, validation.data);
}

/**
 * Delete an agent
 */
export async function deleteAgent(id: AgentId): Promise<Result<void>> {
  return apiClient.delete(`/agents/${id}`);
}
```

## 5. Custom Hook Patterns

### Data Fetching Hooks
*   **REQUIRED:** Create reusable hooks for data fetching
*   **MANDATORY:** Implement proper loading and error states
*   **CRITICAL:** Use React 18 concurrent features where appropriate
*   **REQUIRED:** Handle cleanup and cancellation properly

```typescript
// hooks/use-agents.ts
import { useState, useEffect, useCallback } from 'react';
import * as agentApi from '../api/agents';
import { Agent, AgentCreate, AgentUpdate, AgentListParams } from '../api/agents';
import { AgentId } from '../types/common';

export interface UseAgentsResult {
  agents: Agent[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  createAgent: (data: AgentCreate) => Promise<boolean>;
  updateAgent: (id: AgentId, data: AgentUpdate) => Promise<boolean>;
  deleteAgent: (id: AgentId) => Promise<boolean>;
}

export function useAgents(params: AgentListParams = {}): UseAgentsResult {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = useCallback(async () => {
    setLoading(true);
    setError(null);

    const result = await agentApi.listAgents(params);

    if (result.success) {
      setAgents(result.data);
    } else {
      setError(result.error.message);
    }

    setLoading(false);
  }, [params]);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const createAgent = useCallback(async (data: AgentCreate): Promise<boolean> => {
    const result = await agentApi.createAgent(data);

    if (result.success) {
      setAgents(prev => [...prev, result.data]);
      return true;
    } else {
      setError(result.error.message);
      return false;
    }
  }, []);

  const updateAgent = useCallback(async (
    id: AgentId, 
    data: AgentUpdate
  ): Promise<boolean> => {
    const result = await agentApi.updateAgent(id, data);

    if (result.success) {
      setAgents(prev =>
        prev.map(agent =>
          agent.id === id ? result.data : agent
        )
      );
      return true;
    } else {
      setError(result.error.message);
      return false;
    }
  }, []);

  const deleteAgent = useCallback(async (id: AgentId): Promise<boolean> => {
    const result = await agentApi.deleteAgent(id);

    if (result.success) {
      setAgents(prev => prev.filter(agent => agent.id !== id));
      return true;
    } else {
      setError(result.error.message);
      return false;
    }
  }, []);

  return {
    agents,
    loading,
    error,
    refetch: fetchAgents,
    createAgent,
    updateAgent,
    deleteAgent,
  };
}

// Single agent hook
export function useAgent(id: AgentId | null) {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setAgent(null);
      return;
    }

    let cancelled = false;

    async function fetchAgent() {
      setLoading(true);
      setError(null);

      const result = await agentApi.getAgent(id);

      if (cancelled) return;

      if (result.success) {
        setAgent(result.data);
      } else {
        setError(result.error.message);
      }

      setLoading(false);
    }

    fetchAgent();

    return () => {
      cancelled = true;
    };
  }, [id]);

  return { agent, loading, error };
}
```

## 6. Utility Functions

### Formatting and Display Utilities
*   **REQUIRED:** Create consistent formatting utilities
*   **MANDATORY:** Handle edge cases and null values
*   **CRITICAL:** Use internationalization-friendly patterns
*   **REQUIRED:** Provide comprehensive type safety

```typescript
// utils/format.ts
export function formatDate(
  date: Date | string | null,
  options: Intl.DateTimeFormatOptions = {}
): string {
  if (!date) return 'Never';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) {
    return 'Invalid date';
  }

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    ...options,
  };

  return new Intl.DateTimeFormat('en-US', defaultOptions).format(dateObj);
}

export function formatRelativeTime(date: Date | string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);

  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
  
  return formatDate(dateObj, { month: 'short', day: 'numeric' });
}

export function formatNumber(
  value: number | null | undefined,
  options: Intl.NumberFormatOptions = {}
): string {
  if (value === null || value === undefined) return '—';
  
  return new Intl.NumberFormat('en-US', options).format(value);
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

export function capitalizeFirst(text: string): string {
  if (!text) return '';
  return text.charAt(0).toUpperCase() + text.slice(1);
}

// Status badge formatting
export function getStatusColor(status: string): string {
  const statusColors: Record<string, string> = {
    active: 'bg-green-100 text-green-800',
    inactive: 'bg-gray-100 text-gray-800',
    training: 'bg-blue-100 text-blue-800',
    error: 'bg-red-100 text-red-800',
  };
  
  return statusColors[status] || 'bg-gray-100 text-gray-800';
}
```

## 7. Storage Utilities

### Client-Side Storage
*   **REQUIRED:** Provide type-safe storage utilities
*   **MANDATORY:** Handle storage failures gracefully
*   **CRITICAL:** Implement proper serialization/deserialization
*   **REQUIRED:** Use consistent key naming conventions

```typescript
// utils/storage.ts
type StorageValue = string | number | boolean | object | null;

class TypedStorage {
  constructor(private storage: Storage) {}

  setItem<T extends StorageValue>(key: string, value: T): boolean {
    try {
      const serializedValue = JSON.stringify(value);
      this.storage.setItem(key, serializedValue);
      return true;
    } catch (error) {
      console.error('Failed to store item:', error);
      return false;
    }
  }

  getItem<T extends StorageValue>(key: string): T | null {
    try {
      const item = this.storage.getItem(key);
      if (item === null) return null;
      
      return JSON.parse(item) as T;
    } catch (error) {
      console.error('Failed to retrieve item:', error);
      return null;
    }
  }

  removeItem(key: string): boolean {
    try {
      this.storage.removeItem(key);
      return true;
    } catch (error) {
      console.error('Failed to remove item:', error);
      return false;
    }
  }

  clear(): boolean {
    try {
      this.storage.clear();
      return true;
    } catch (error) {
      console.error('Failed to clear storage:', error);
      return false;
    }
  }
}

// Singleton instances
export const localStorage = typeof window !== 'undefined' 
  ? new TypedStorage(window.localStorage)
  : null;

export const sessionStorage = typeof window !== 'undefined'
  ? new TypedStorage(window.sessionStorage)
  : null;

// Application-specific storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'agentflow_auth_token',
  USER_PREFERENCES: 'agentflow_user_prefs',
  RECENT_AGENTS: 'agentflow_recent_agents',
  THEME: 'agentflow_theme',
} as const;
```

## 8. Configuration Management

### Environment Configuration
*   **REQUIRED:** Validate environment variables at startup
*   **MANDATORY:** Provide type-safe configuration access
*   **CRITICAL:** Handle missing required configuration gracefully
*   **REQUIRED:** Document all configuration options

```typescript
// config.ts
import { z } from 'zod';

const configSchema = z.object({
  apiUrl: z.string().url().default('http://localhost:8000'),
  appName: z.string().default('AgentFlow'),
  environment: z.enum(['development', 'staging', 'production']).default('development'),
  enableAnalytics: z.boolean().default(false),
  logLevel: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  maxRetries: z.number().min(0).max(10).default(3),
  requestTimeout: z.number().min(1000).max(60000).default(30000),
});

type Config = z.infer<typeof configSchema>;

function loadConfig(): Config {
  const rawConfig = {
    apiUrl: process.env.NEXT_PUBLIC_API_URL,
    appName: process.env.NEXT_PUBLIC_APP_NAME,
    environment: process.env.NODE_ENV,
    enableAnalytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
    logLevel: process.env.NEXT_PUBLIC_LOG_LEVEL,
    maxRetries: process.env.NEXT_PUBLIC_MAX_RETRIES 
      ? parseInt(process.env.NEXT_PUBLIC_MAX_RETRIES, 10) 
      : undefined,
    requestTimeout: process.env.NEXT_PUBLIC_REQUEST_TIMEOUT
      ? parseInt(process.env.NEXT_PUBLIC_REQUEST_TIMEOUT, 10)
      : undefined,
  };

  const result = configSchema.safeParse(rawConfig);
  
  if (!result.success) {
    console.error('Invalid configuration:', result.error.issues);
    throw new Error('Configuration validation failed');
  }

  return result.data;
}

export const config = loadConfig();
export default config;
```

## 9. Forbidden Patterns
*   **NEVER** use `any` type without explicit documentation and justification
*   **NEVER** ignore Promise rejections in utility functions
*   **NEVER** mutate function parameters or external state
*   **NEVER** create utilities that depend on React hooks outside of custom hooks
*   **NEVER** hardcode configuration values in utility modules
*   **NEVER** skip error handling in API client functions
*   **NEVER** expose sensitive data through client-side utilities
*   **NEVER** use synchronous storage operations in utility functions

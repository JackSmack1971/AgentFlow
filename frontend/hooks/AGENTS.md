# AGENTS.md: Frontend Custom Hooks Development Guide

This document provides essential context for AI models working with custom React hooks in the AgentFlow frontend. These guidelines ensure consistent patterns, optimal performance, and maintainable client-side state management.

## 1. Project Overview & Purpose
*   **Primary Goal:** Custom React hooks for AgentFlow's Next.js 14+ frontend that manage client-side state, API interactions, and real-time streaming for AI agent workflows, memory operations, and knowledge management
*   **Business Domain:** Frontend State Management, React Hooks Architecture, Real-time UI Updates, Agent Interaction Patterns
*   **Key Features:** 
    - Agent execution hooks with streaming response handling (`useAgentRunner`)
    - Memory management hooks with real-time updates and optimistic UI patterns
    - Authentication state management with session persistence
    - Knowledge upload and search hooks with progress tracking
    - WebSocket and EventSource integration for real-time data flows

## 2. Core Technologies & Stack
*   **Languages:** TypeScript 5.x (strict mode), JavaScript ES2023
*   **Frameworks & Runtimes:** 
    - React 18+ with concurrent features and Suspense
    - Next.js 14+ App Router with Server/Client component boundaries
    - React Hook Form for complex form state management
*   **Key Libraries/Dependencies:** 
    - `zod` - Runtime validation and type safety for hook parameters
    - `@tanstack/react-query` or SWR - Server state caching and synchronization
    - Custom API client with TypeScript - HTTP operations with proper error handling
    - EventSource/WebSocket - Real-time streaming for agent responses
    - React Testing Library + Jest - Hook testing with `@testing-library/react-hooks`
*   **Validation & Type Safety:** Zod schemas for all hook inputs, strict TypeScript with `noUncheckedIndexedAccess`
*   **Package Manager:** npm (JavaScript/TypeScript dependencies)
*   **Client Boundary:** All hooks require `'use client'` directive - server components cannot use hooks

## 3. Custom Hooks Architecture & Patterns
*   **Overall Architecture:** Hooks follow a layered architecture - data fetching hooks at the base, business logic hooks in the middle, and UI interaction hooks at the top. Each hook has a single responsibility with clear dependencies and error boundaries.
*   **Directory Structure Philosophy:**
    *   `/frontend/hooks/` - All custom hooks with consistent naming (`use-*` prefix)
    *   `/frontend/hooks/api/` - HTTP client interaction hooks (useAgents, useMemory, useKnowledge)
    *   `/frontend/hooks/auth/` - Authentication and session management hooks
    *   `/frontend/hooks/streaming/` - Real-time data streaming hooks (WebSocket, EventSource)
    *   `/frontend/hooks/forms/` - Form state and validation hooks with Zod integration
    *   `/frontend/hooks/utils/` - Utility hooks (useLocalStorage, useDebounce, useInterval)
*   **Hook Organization Pattern:** 
    - Business domain-specific hooks (agent workflows, memory operations, knowledge management)
    - Each hook file exports the main hook and related TypeScript interfaces
    - Hooks compose smaller utility hooks rather than implementing everything inline
*   **Common Hook Patterns:**
    - **Streaming Responses:** `useAgentRunner` handles chunked responses with `onChunk` callbacks
    - **Optimistic Updates:** Memory and knowledge hooks update UI immediately, then sync with server
    - **Error Boundaries:** All hooks return structured error states with user-friendly messages
    - **Loading States:** Multi-level loading states (idle, loading, streaming, error, success)
    - **Real-time Sync:** EventSource integration for live updates without polling

## 4. Hook Development Conventions & Style Guide
*   **Formatting:** TypeScript strict mode with Biome formatting. No `any` types, prefer type inference with explicit return types for public hooks
*   **Naming Conventions:** 
    - Hook files: `use-{domain}-{action}.ts` (e.g., `use-agent-runner.ts`, `use-memory-search.ts`)
    - Hook functions: `use{Domain}{Action}` PascalCase (e.g., `useAgentRunner`, `useMemorySearch`)
    - State variables: `camelCase` with descriptive names (`isLoading`, `streamingResponse`, `searchResults`)
    - Types/Interfaces: `PascalCase` with descriptive suffixes (`AgentRunnerHook`, `MemorySearchOptions`)
*   **Hook Structure Pattern:**
    ```typescript
    // use-agent-runner.ts
    import { useState, useCallback } from 'react';
    import { z } from 'zod';
    
    const runOptionsSchema = z.object({
      onChunk: z.function().optional(),
      timeout: z.number().default(30000)
    });
    
    export interface UseAgentRunnerReturn {
      run: (prompt: string, options?: RunOptions) => Promise<string>;
      isRunning: boolean;
      currentResponse: string;
      error: string | null;
    }
    
    export function useAgentRunner(): UseAgentRunnerReturn {
      const [isRunning, setIsRunning] = useState(false);
      const [currentResponse, setCurrentResponse] = useState('');
      const [error, setError] = useState<string | null>(null);
      
      const run = useCallback(async (prompt: string, options?: RunOptions) => {
        // Implementation with proper error handling
      }, []);
      
      return { run, isRunning, currentResponse, error };
    }
    ```
*   **Error Handling in Hooks:** 
    - Use structured error states: `{ error: string | null, isError: boolean }`
    - Validate all inputs with Zod schemas before API calls
    - Catch and transform API errors into user-friendly messages
    - Provide error recovery mechanisms where appropriate

## 5. Key Hook Files & Integration Points
*   **Core Agent Hooks:**
    - `use-agent-runner.ts` - Execute agent workflows with streaming responses
    - `use-agent-list.ts` - Fetch and manage agent collections with caching
    - `use-agent-builder.ts` - Multi-step agent creation with form state management
*   **Memory Management Hooks:**
    - `use-memory-browser.ts` - Search, edit, and delete memory items with real-time updates
    - `use-memory-stream.ts` - EventSource integration for live memory updates
*   **Authentication Hooks:**
    - `use-auth.ts` - Login, logout, and session state management
    - `use-protected-route.ts` - Route protection with redirect logic
*   **API Client Integration:** All hooks use a shared `ApiClient` instance with consistent error handling and request/response interceptors

## 6. Hook Testing & Development Workflow
*   **Local Development Environment:** 
    1. Start Next.js dev server: `cd frontend && npm run dev`
    2. Storybook for hook isolation: `npm run storybook` (if configured)
    3. Test individual hooks: `npm run test -- --watch hooks/`
*   **Hook Testing Strategy:** **All custom hooks require corresponding unit tests.**
    ```typescript
    // use-agent-runner.test.ts
    import { renderHook, act } from '@testing-library/react';
    import { useAgentRunner } from './use-agent-runner';
    
    // Mock the API client
    jest.mock('../../lib/api', () => ({
      default: jest.fn().mockImplementation(() => ({
        agents: { run: jest.fn() }
      }))
    }));
    
    describe('useAgentRunner', () => {
      it('handles streaming responses correctly', async () => {
        const { result } = renderHook(() => useAgentRunner());
        
        await act(async () => {
          await result.current.run('test prompt', {
            onChunk: (chunk) => expect(chunk).toBeDefined()
          });
        });
        
        expect(result.current.isRunning).toBe(false);
        expect(result.current.error).toBe(null);
      });
    });
    ```
*   **Integration with Components:** 
    - Test hooks within actual components using React Testing Library
    - Mock external dependencies (API calls, EventSource, WebSocket)
    - Use MSW (Mock Service Worker) for realistic API response testing
*   **Performance Testing:** 
    - Monitor hook re-render frequency with React DevTools Profiler
    - Test memory cleanup in hooks that manage subscriptions or timers
    - Validate that hooks don't cause unnecessary component re-renders

## 7. Hook Development Best Practices & AI Collaboration Guidelines
*   **Client-Side Boundary Management:**
    - **ALWAYS use `'use client'` directive** at the top of hook files
    - **NEVER call hooks in Server Components** - only in Client Components
    - **Validate server/client boundaries** when passing data between components and hooks
*   **State Management Patterns:**
    - **Prefer local state over global state** - use hooks for component-scoped state
    - **Use React Query/SWR for server state** - don't duplicate server data in local state
    - **Implement optimistic updates** for better UX with proper rollback on errors
    - **Debounce user input** in search and form hooks to reduce API calls
*   **Streaming and Real-time Updates:**
    ```typescript
    // EventSource pattern for real-time updates
    useEffect(() => {
      const eventSource = new EventSource('/api/memory/stream');
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // Update local state with new data
      };
      return () => eventSource.close();
    }, []);
    ```
*   **Error Recovery and User Experience:**
    - **Provide retry mechanisms** for failed API calls
    - **Show meaningful error messages** - transform API errors to user-friendly text
    - **Implement graceful degradation** when real-time features fail
    - **Handle network connectivity issues** with appropriate fallback states
*   **Performance Optimization:**
    - **Use `useCallback` and `useMemo`** appropriately to prevent unnecessary re-renders
    - **Implement proper cleanup** in `useEffect` for subscriptions and timers
    - **Avoid creating objects in render** - move object creation to useCallback/useMemo
    - **Consider `useTransition`** for non-urgent state updates that might cause UI lag
*   **Security & Data Handling:**
    - **Validate all user inputs** with Zod schemas before processing
    - **Never log sensitive data** in hooks (tokens, passwords, personal information)
    - **Sanitize data from external sources** (API responses, user input)
    - **Handle authentication state securely** - clear sensitive data on logout
*   **Testing Requirements:**
    - **Mock external dependencies** - API clients, EventSource, WebSocket, timers
    - **Test error scenarios** - network failures, invalid responses, authentication errors
    - **Validate cleanup behavior** - ensure subscriptions and timers are properly disposed
    - **Test concurrent operations** - multiple API calls, race conditions, cleanup during requests
*   **Forbidden Patterns:**
    - **NEVER use hooks in Server Components** - will cause hydration errors
    - **NEVER mutate props or state directly** - always use setter functions
    - **NEVER create side effects in render** - use useEffect or event handlers
    - **NEVER ignore TypeScript errors** with `@ts-ignore` - fix the underlying issue
    - **NEVER use `any` type** - prefer `unknown` and type guards for dynamic data
*   **Development Guidelines:**
    - **Keep hooks focused and single-purpose** - compose multiple hooks rather than creating monolithic ones
    - **Document complex hook behavior** with JSDoc comments and usage examples
    - **Provide TypeScript interfaces** for all hook parameters and return values
    - **Test hooks in isolation** before integrating with components
    - **Monitor hook performance** with React DevTools and address re-render issues promptly

## 8. Hook Integration Validation Checklist
Before completing any custom hook development, ensure:

- [ ] Hook follows `use{Domain}{Action}` naming convention with proper TypeScript types
- [ ] All inputs validated with Zod schemas and errors handled gracefully
- [ ] Hook includes comprehensive tests with success/error scenarios and cleanup validation
- [ ] Real-time features (EventSource/WebSocket) properly handle connection errors and reconnection
- [ ] Hook integrates properly with Next.js App Router client/server boundaries
- [ ] Performance optimized with appropriate use of useCallback/useMemo for stable references
- [ ] Security considerations addressed - no sensitive data logging, proper input sanitization
- [ ] Error states provide actionable feedback to users with retry mechanisms where appropriate
- [ ] Hook composes well with other hooks and doesn't create circular dependencies
- [ ] Documentation includes usage examples and integration patterns for component developers

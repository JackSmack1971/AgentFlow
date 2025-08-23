# Project Overview & Purpose

This file provides essential guidance for AI agents working with UI components throughout the AgentFlow frontend. AgentFlow is a unified AI agent development platform that integrates six leading frameworks to reduce agent development time by 60-80%. The UI architecture emphasizes **React Server Components (RSC)** with minimal client-side JavaScript, sophisticated interactive components for workflow orchestration, and enterprise-grade real-time interfaces. All components follow Next.js 14+ App Router patterns with strong TypeScript safety and modern Rust-based tooling.

## Architecture & Key Files

**Primary Technologies:** Next.js 14+ App Router, React 18+ Server Components, TypeScript 5.x (strict), Tailwind CSS, Biome (Rust-based linting), Zustand (client state), TanStack Query (API state)
**Architecture Pattern:** Server-first with selective client hydration, three-column responsive layout, progressive disclosure

### Critical Component Structure
```
frontend/components/
├── ui/                     # Foundation design system (Server Components preferred)
│   ├── server/                # Server-only UI components
│   │   ├── agent-card.tsx        # Dashboard agent cards (RSC)
│   │   ├── run-history-table.tsx # Server-rendered data tables
│   │   ├── metrics-dashboard.tsx # Performance visualization (RSC)
│   │   └── knowledge-grid.tsx    # Document display (RSC)
│   ├── client/               # Client components (minimize usage)
│   │   ├── interactive-button.tsx # Buttons requiring state ('use client')
│   │   ├── form-input.tsx        # Form inputs with validation
│   │   ├── toast-notifications.tsx # Real-time notifications
│   │   └── modal-dialog.tsx      # Interactive modals
│   └── shared/               # Isomorphic components
│       ├── badge.tsx             # Status indicators
│       ├── card.tsx              # Content containers
│       ├── progress.tsx          # Progress indicators
│       └── skeleton.tsx          # Loading placeholders
├── interactive/            # Complex client-side components
│   ├── node-canvas.tsx        # Visual workflow editor ('use client')
│   ├── streaming-terminal.tsx # Real-time agent response display
│   ├── knowledge-graph.tsx    # Interactive graph visualization  
│   ├── trace-viewer.tsx       # Hierarchical execution traces
│   ├── memory-browser.tsx     # Multi-scope memory management
│   └── semantic-search.tsx    # Hybrid search with real-time results
├── server-actions/         # Next.js Server Actions
│   ├── agent-actions.ts       # Create/update/delete agents
│   ├── memory-actions.ts      # Memory management operations
│   ├── knowledge-actions.ts   # Document upload/processing
│   └── auth-actions.ts        # Authentication operations
├── providers/              # React Context providers (client-side)
│   ├── query-provider.tsx     # TanStack Query setup
│   ├── toast-provider.tsx     # Toast notification context
│   └── theme-provider.tsx     # Dark/light mode context
└── hooks/                  # Custom hooks
    ├── use-websocket.ts       # WebSocket connection management
    ├── use-canvas-interactions.ts # Canvas event handling
    ├── use-streaming.ts       # EventSource stream handling
    └── use-optimistic-updates.ts # Optimistic UI patterns
```

**Server-First Architecture:**
- **Server Components** handle data fetching and initial rendering
- **Server Actions** manage all mutations and form submissions  
- **Client Components** only for interactivity requiring useState/useEffect
- **Progressive Enhancement** ensures functionality without JavaScript

## Development Environment & Commands

**Prerequisites:** Node.js 20+, TypeScript 5.x, Biome (Rust-based tooling), Docker for backend services

### Next.js Development Workflow
```bash
# Start development with type-safe routing enabled
npm run dev

# Type checking with strict TypeScript configuration
npm run type-check

# Biome linting and formatting (Rust-based, fast)
npm run lint       # Check code quality
npm run format     # Auto-format code

# Server Component testing
npm run test:server

# Client Component testing with React Testing Library
npm run test:client

# Integration testing with Server Actions
npm run test:integration

# Build with RSC optimization
npm run build

# Analyze bundle for client/server code split
npm run analyze
```

### Data Fetching & State Management Commands
```bash
# Test Server Actions with form validation
npm run test:actions

# Test TanStack Query integration
npm run test:queries

# Test WebSocket real-time features
npm run test:websockets

# Performance testing for streaming components
npm run test:streaming-performance
```

**CRITICAL:** All Server Components MUST be tested for proper data fetching and SSR compatibility. Client components require testing for hydration and progressive enhancement.

## Code Style & Conventions

### Next.js App Router Standards (MANDATORY)

**1. Server Components by Default (Minimize 'use client')**
```tsx
// ✅ PREFERRED: Server Component for static/data-driven UI
// No 'use client' needed
export default async function AgentDashboard() {
  // Direct database/API access on server
  const agents = await getAgents(); // No fetch() needed
  const runs = await getRecentRuns();
  
  return (
    <div className="grid gap-6">
      <AgentGrid agents={agents} />
      <RunHistoryTable runs={runs} />
    </div>
  );
}

// ✅ Server Action for mutations
async function createAgent(formData: FormData) {
  'use server';
  
  const validatedData = CreateAgentSchema.parse({
    name: formData.get('name'),
    description: formData.get('description'),
  });
  
  await db.agents.create(validatedData);
  revalidatePath('/agents');
}

// ❌ AVOID: Client Component unless absolutely necessary
'use client';
export default function InteractiveCanvas() {
  const [nodes, setNodes] = useState([]); // Only when state required
  // ... client-side logic
}
```

**2. TypeScript Strict Standards (MANDATORY)**
```tsx
// ✅ Comprehensive TypeScript interfaces
interface AgentCardProps {
  agent: {
    id: string;
    name: string;
    description: string | null; // Explicit null handling
    status: 'active' | 'inactive' | 'training' | 'error';
    modelProvider: 'openai' | 'anthropic' | 'google' | 'local';
    runCount: number;
    createdAt: Date;
    metadata?: Record<string, unknown>; // Strict unknown over any
  };
  onEdit?: (agentId: string) => void;
  onDelete?: (agentId: string) => void;
  className?: string;
}

// ✅ Zod validation for Server Actions
import { z } from 'zod';

const CreateAgentSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().optional(),
  modelProvider: z.enum(['openai', 'anthropic', 'google', 'local']),
  tools: z.array(z.string()).optional(),
});

type CreateAgentInput = z.infer<typeof CreateAgentSchema>;
```

**3. State Management Patterns**
```tsx
// ✅ URL searchParams for server-side state
interface PageProps {
  searchParams: { 
    status?: string; 
    page?: string; 
    search?: string; 
  };
}

export default function AgentsPage({ searchParams }: PageProps) {
  const agents = await getAgents({
    status: searchParams.status as AgentStatus,
    page: Number(searchParams.page) || 1,
    search: searchParams.search,
  });
  
  return <AgentList agents={agents} />;
}

// ✅ Zustand for client-side global state
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  toggleSidebar: () => void;
  setTheme: (theme: UIState['theme']) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'system',
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
    }),
    { name: 'ui-settings' }
  )
);

// ✅ TanStack Query for API data fetching (client-side)
'use client';
import { useQuery } from '@tanstack/react-query';

export function useAgentRuns(agentId: string) {
  return useQuery({
    queryKey: ['agent-runs', agentId],
    queryFn: () => fetch(`/api/agents/${agentId}/runs`).then(res => res.json()),
    staleTime: 30_000, // 30 seconds
    refetchOnWindowFocus: false,
  });
}
```

### Error Handling & Validation (CRITICAL)
```tsx
// ✅ Server Action with Zod validation and error handling
async function updateAgent(agentId: string, formData: FormData) {
  'use server';
  
  try {
    const validatedData = UpdateAgentSchema.parse({
      name: formData.get('name'),
      description: formData.get('description'),
    });
    
    const agent = await db.agents.update({
      where: { id: agentId },
      data: validatedData,
    });
    
    revalidatePath('/agents');
    return { success: true, agent };
    
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        success: false,
        error: 'Invalid form data',
        fieldErrors: error.flatten().fieldErrors,
      };
    }
    
    console.error('Failed to update agent:', error);
    return { success: false, error: 'Failed to update agent' };
  }
}

// ✅ Error boundaries for complex components
'use client';
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error, resetErrorBoundary }: any) {
  return (
    <div role="alert" className="p-4 border border-red-200 rounded-lg">
      <h2 className="text-lg font-semibold text-red-800">Something went wrong:</h2>
      <pre className="mt-2 text-sm text-red-600">{error.message}</pre>
      <button 
        onClick={resetErrorBoundary}
        className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
      >
        Try again
      </button>
    </div>
  );
}

export function ProtectedComponent({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      {children}
    </ErrorBoundary>
  );
}
```

### Performance & Streaming Patterns
```tsx
// ✅ Streaming with Suspense for progressive loading
import { Suspense } from 'react';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Immediate render */}
      <DashboardHeader />
      
      {/* Progressive loading with fallbacks */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Suspense fallback={<AgentGridSkeleton />}>
          <AgentGrid />
        </Suspense>
        
        <Suspense fallback={<MetricsDashboardSkeleton />}>
          <MetricsDashboard />
        </Suspense>
      </div>
      
      {/* Heavy component loads last */}
      <Suspense fallback={<RunHistorySkeleton />}>
        <RunHistoryTable />
      </Suspense>
    </div>
  );
}

// ✅ Parallel data fetching (not waterfall)
export default async function AgentDetailPage({ params }: { params: { id: string } }) {
  // Initiate all requests in parallel
  const [agent, runs, metrics] = await Promise.all([
    getAgent(params.id),
    getAgentRuns(params.id),
    getAgentMetrics(params.id),
  ]);
  
  return (
    <div>
      <AgentHeader agent={agent} />
      <RunsTable runs={runs} />
      <MetricsChart data={metrics} />
    </div>
  );
}
```

## Testing & Validation Protocol

### Next.js Testing Framework
**Testing Stack:** Jest + React Testing Library + Playwright (E2E) + MSW (API mocking)
**Coverage Requirements:** 
- Server Components: ≥90% (data fetching, SSR)
- Client Components: ≥95% (interactions, state)
- Server Actions: ≥95% (validation, mutations)

### Server Component Testing
```tsx
// server-component.test.tsx
import { render, screen } from '@testing-library/react';
import AgentDashboard from './agent-dashboard';

// Mock Next.js modules
jest.mock('next/navigation', () => ({
  redirect: jest.fn(),
}));

describe('AgentDashboard (Server Component)', () => {
  it('renders agent data from server', async () => {
    // Mock the server-side data fetching
    const mockAgents = [
      { id: '1', name: 'Test Agent', status: 'active' as const },
    ];
    
    jest.spyOn(require('../lib/agents'), 'getAgents').mockResolvedValue(mockAgents);
    
    render(await AgentDashboard());
    
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
  });

  it('handles empty agent list gracefully', async () => {
    jest.spyOn(require('../lib/agents'), 'getAgents').mockResolvedValue([]);
    
    render(await AgentDashboard());
    
    expect(screen.getByText(/no agents found/i)).toBeInTheDocument();
  });
});
```

### Server Action Testing
```tsx
// server-action.test.ts
import { createAgent } from './agent-actions';

describe('createAgent Server Action', () => {
  it('creates agent with valid data', async () => {
    const formData = new FormData();
    formData.set('name', 'Test Agent');
    formData.set('description', 'Test description');
    formData.set('modelProvider', 'openai');
    
    const result = await createAgent(formData);
    
    expect(result.success).toBe(true);
    expect(result.agent?.name).toBe('Test Agent');
  });

  it('validates form data with Zod', async () => {
    const formData = new FormData();
    formData.set('name', ''); // Invalid: empty name
    
    const result = await createAgent(formData);
    
    expect(result.success).toBe(false);
    expect(result.fieldErrors?.name).toBeDefined();
  });
});
```

### Client Component Testing with Real-time Features
```tsx
// streaming-terminal.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { StreamingTerminal } from './streaming-terminal';

describe('StreamingTerminal', () => {
  it('handles EventSource streaming', async () => {
    const mockEventSource = {
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      close: jest.fn(),
    };
    
    global.EventSource = jest.fn(() => mockEventSource) as any;
    
    render(<StreamingTerminal agentId="test" runId="run123" />);
    
    expect(global.EventSource).toHaveBeenCalledWith('/api/runs/run123/stream');
    expect(mockEventSource.addEventListener).toHaveBeenCalledWith('message', expect.any(Function));
  });

  it('cleans up EventSource on unmount', () => {
    const mockEventSource = {
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      close: jest.fn(),
    };
    
    global.EventSource = jest.fn(() => mockEventSource) as any;
    
    const { unmount } = render(<StreamingTerminal agentId="test" runId="run123" />);
    
    unmount();
    
    expect(mockEventSource.close).toHaveBeenCalled();
  });
});
```

### Validation Commands (MANDATORY EXECUTION)
```bash
# TypeScript strict type checking
npm run type-check

# Biome linting (Rust-based, fast)
npm run lint

# Server Component tests
npm run test:server

# Client Component and interaction tests  
npm run test:client

# Server Action validation and mutation tests
npm run test:actions

# End-to-end testing with Playwright
npm run test:e2e

# Accessibility testing with axe-core
npm run test:a11y

# Performance testing for streaming/real-time features
npm run test:performance

# Bundle analysis for RSC optimization
npm run analyze
```

**CRITICAL:** All tests MUST pass before completing tasks. Pay special attention to Server Component SSR compatibility and Server Action validation.

## Pull Request (PR) Instructions

### PR Title Format (MANDATORY)
```
[UI-RSC] <Component Type>: <Description>
[UI-Client] <Component Type>: <Description> 
[Actions] <Feature>: <Description>

Examples:
[UI-RSC] Dashboard: Add agent grid with server-side filtering
[UI-Client] Canvas: Implement real-time node collaboration
[Actions] Agents: Add Zod validation for agent creation
```

### Required PR Sections
```markdown
## Description:
Brief description focusing on Server/Client component distinction and data flow.

## Architecture Changes:
- [ ] Server Component implementation with proper data fetching
- [ ] Client Component with justified 'use client' usage
- [ ] Server Actions with Zod validation
- [ ] TypeScript interfaces with strict typing
- [ ] Error boundaries for complex interactions

## Testing Completed:
- [ ] Server Component SSR testing
- [ ] Client Component interaction testing  
- [ ] Server Action validation testing
- [ ] Real-time feature connection/cleanup testing
- [ ] E2E testing with Playwright
- [ ] Accessibility testing with axe-core

## Performance Validation:
- [ ] Bundle analysis shows appropriate RSC/Client split
- [ ] Streaming/Suspense boundaries tested
- [ ] WebSocket connections properly managed
- [ ] No hydration mismatches
- [ ] Progressive enhancement verified

## Accessibility Checklist:
- [ ] Semantic HTML with proper ARIA labels
- [ ] Keyboard navigation for all interactive elements
- [ ] Screen reader compatibility with dynamic content
- [ ] Color contrast meets WCAG 2.1 AA standards
- [ ] Form validation errors properly announced

## Screenshots/Recordings:
[Include evidence of Server/Client rendering, streaming behavior, error states]
```

## Security & Non-Goals

### Security Standards
- **CRITICAL:** Use Server Actions exclusively for mutations (never client-side API calls)
- **MANDATORY:** Validate all inputs with Zod schemas on the server
- **REQUIRED:** Use React's taint APIs to prevent sensitive data client exposure
- **CRITICAL:** Implement proper CSRF protection for Server Actions
- **REQUIRED:** Sanitize all real-time data from WebSocket/EventSource connections

### Next.js Security Patterns
```tsx
// ✅ Secure Server Action with validation
async function updateAgentSettings(formData: FormData) {
  'use server';
  
  // Authentication check
  const session = await getServerSession();
  if (!session?.user) {
    throw new Error('Unauthorized');
  }
  
  // Input validation
  const data = UpdateSettingsSchema.parse({
    name: formData.get('name'),
    // ... other fields
  });
  
  // Authorization check
  const agent = await getAgent(data.agentId);
  if (agent.userId !== session.user.id) {
    throw new Error('Forbidden');
  }
  
  // Safe operation
  return await updateAgent(data);
}
```

### Non-Goals (FORBIDDEN)
- **FORBIDDEN:** Using 'use client' without clear justification for interactivity
- **FORBIDDEN:** Client-side mutations without Server Actions
- **FORBIDDEN:** useEffect for data fetching in Server Components
- **FORBIDDEN:** Global state (Redux) for server-side state
- **FORBIDDEN:** Custom CSS without Tailwind utility classes
- **FORBIDDEN:** Components without proper TypeScript strict typing
- **FORBIDDEN:** Real-time features without connection cleanup
- **FORBIDDEN:** Form submissions without Zod validation
- **FORBIDDEN:** API routes when Server Actions suffice
- **FORBIDDEN:** Direct database queries in Client Components

**Architecture Principle:** Server-first with selective client hydration. Every 'use client' directive must be justified by genuine interactivity needs. All data mutations flow through Server Actions with comprehensive validation.

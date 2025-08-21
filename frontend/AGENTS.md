# AgentFlow Frontend Implementation PRP

**Feature Goal**: Implement the complete Next.js + TypeScript frontend application for AgentFlow to provide an intuitive user interface for agent creation, memory management, workflow design, and platform monitoring.

**Deliverable**: Production-ready Next.js frontend application with App Router architecture, matching the comprehensive specifications outlined in `frontend/AGENTS.md` and fulfilling the user interface requirements from the Product Requirements Document.

**Success Definition**: Users can create, configure, test, and deploy AI agents through a visual interface in under 10 minutes, with full functionality for memory management, knowledge base integration, and workflow orchestration.

## User Persona

**Target User**: Technical Product Managers and Senior AI/ML Engineers (80% combined user base from PRD)

**Use Case**: Creating and managing AI agents through visual interfaces rather than code-only approaches

**User Journey**: 
1. User logs into AgentFlow dashboard
2. Selects agent template from library or creates from scratch
3. Configures agent settings through guided wizard
4. Tests agent in conversation simulator
5. Deploys agent and monitors performance through analytics dashboard

**Pain Points Addressed**: 
- Eliminates need for complex framework integration coding
- Provides visual feedback for agent behavior and memory state
- Simplifies deployment and monitoring through unified interface

## Why

- **Critical Gap**: Backend API is fully functional but completely inaccessible to end users without a frontend interface
- **User Experience**: Visual interfaces reduce agent development time by 60-80% compared to code-only approaches (per PRD requirements)
- **Platform Completion**: Frontend represents the final major component needed to achieve the stated business goals of <5 minutes time-to-first-agent
- **Revenue Impact**: User interface directly enables the target of 100+ enterprise customers and $2M ARR by providing accessible agent creation tools

## What

A comprehensive Next.js + TypeScript frontend application implementing:

- **Dashboard Interface**: Overview of agents, memory usage, knowledge bases, and system analytics
- **Agent Builder**: Visual drag-and-drop interface for agent creation and configuration
- **Memory Management**: Interface for viewing, editing, and analyzing multi-level memory (user/agent/session)
- **Knowledge Base Management**: Document upload, organization, search, and integration tools
- **Workflow Designer**: Visual node-based editor for complex agent workflows
- **Testing & Debugging**: Conversation simulator, performance profiler, and real-time debugging tools
- **Deployment Management**: One-click deployment interface with monitoring and analytics
- **User Authentication**: Secure login, registration, and organization management

### Success Criteria

- [ ] Application loads and renders main dashboard in <2 seconds
- [ ] Users can create basic agent through wizard in <5 minutes
- [ ] Agent creation interface supports drag-and-drop workflow design
- [ ] Memory management interface provides real-time view and edit capabilities
- [ ] Knowledge base upload supports drag-and-drop with progress tracking
- [ ] Testing interface provides immediate conversation simulation
- [ ] Deployment interface successfully deploys agents with health monitoring
- [ ] Application achieves >90% user satisfaction score (per PRD target)
- [ ] Mobile-responsive design supports tablets (>768px width) effectively
- [ ] WCAG 2.1 AA accessibility compliance for enterprise requirements

## All Needed Context

### Context Completeness Check

This PRP provides comprehensive frontend implementation context including project structure, technology stack, existing backend APIs, design patterns, accessibility requirements, and security considerations from the detailed specifications in `frontend/AGENTS.md`.

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- file: frontend/AGENTS.md
  why: Complete Next.js App Router architecture, component patterns, and development standards
  critical: TypeScript configuration, accessibility requirements, security patterns, testing strategies

- file: AgentFlow_PRD.md
  why: User personas, success criteria, performance requirements, and business objectives
  pattern: User journey flows, target metrics, feature priorities
  gotcha: <5 minutes time-to-first-agent requirement, >90% satisfaction target

- file: agentflow_frd.md
  why: Detailed functional requirements for each frontend component
  section: FR-2000 (Agent Creation), FR-3000 (Memory Management), FR-5000 (Knowledge Base)
  critical: Specific acceptance criteria and technical specifications

- file: apps/api/app/main.py
  why: FastAPI backend API structure and available endpoints
  pattern: Router organization, authentication flows, response schemas
  gotcha: API authentication requirements, CORS configuration

- file: apps/api/app/models/schemas.py
  why: Pydantic models for TypeScript type generation and API integration
  pattern: Request/response models, validation patterns
  critical: Type safety alignment between backend and frontend
```

### Current Codebase Tree

```bash
.
├── README.md
├── AGENTS.md
├── AgentFlow_PRD.md
├── agentflow_frd.md
├── apps/
│   ├── api/                    # FastAPI backend (implemented)
│   │   ├── app/
│   │   │   ├── main.py         # API entry point with 7 routers
│   │   │   ├── routers/        # auth, memory, rag, agents, health, cache_examples
│   │   │   ├── services/       # Business logic layer
│   │   │   ├── models/         # Pydantic schemas
│   │   │   └── db/             # Database models and migrations
│   │   └── AGENTS.md
│   └── mcp/                    # MCP server (implemented)
│       ├── server.py
│       └── AGENTS.md
├── frontend/                   # Next.js frontend (NOT IMPLEMENTED)
│   └── AGENTS.md              # Complete specification but no code
├── tests/                      # Test suite (implemented)
├── scripts/                    # Development scripts
├── infra/                      # Infrastructure config
├── docker-compose.yml          # 6 services ready
└── pyproject.toml             # Dependencies configured
```

### Desired Codebase Tree with Files to be Added and Responsibility

```bash
frontend/                       # Complete Next.js application
├── package.json               # Dependencies: next, react, typescript, tailwindcss, @types/*
├── tsconfig.json              # Strict TypeScript configuration
├── next.config.js             # Next.js configuration with API proxy
├── tailwind.config.js         # Tailwind CSS configuration
├── app/                       # Next.js App Router
│   ├── layout.tsx             # Root layout with navigation and providers
│   ├── page.tsx               # Dashboard/landing page
│   ├── globals.css            # Global styles and Tailwind imports
│   ├── (dashboard)/           # Dashboard route group
│   │   ├── layout.tsx         # Dashboard layout with sidebar
│   │   ├── agents/            # Agent management pages
│   │   │   ├── page.tsx       # Agent list and overview
│   │   │   ├── create/        # Agent creation wizard
│   │   │   │   └── page.tsx
│   │   │   └── [id]/          # Individual agent management
│   │   │       ├── page.tsx   # Agent details and configuration
│   │   │       ├── test/      # Agent testing interface
│   │   │       │   └── page.tsx
│   │   │       └── deploy/    # Agent deployment interface
│   │   │           └── page.tsx
│   │   ├── memory/            # Memory management pages
│   │   │   ├── page.tsx       # Memory overview and search
│   │   │   └── [id]/          # Individual memory management
│   │   │       └── page.tsx
│   │   ├── knowledge/         # Knowledge base management
│   │   │   ├── page.tsx       # Knowledge base list
│   │   │   ├── upload/        # Document upload interface
│   │   │   │   └── page.tsx
│   │   │   └── [id]/          # Knowledge base details
│   │   │       └── page.tsx
│   │   └── analytics/         # Analytics and monitoring
│   │       └── page.tsx
│   ├── (auth)/                # Authentication pages
│   │   ├── login/
│   │   │   └── page.tsx       # Login form
│   │   └── register/
│   │       └── page.tsx       # Registration form
│   └── api/                   # API route handlers (proxy to backend)
│       ├── auth/
│       │   └── route.ts       # Authentication API proxy
│       └── proxy/
│           └── [...path]/
│               └── route.ts   # Generic API proxy handler
├── components/                # Reusable UI components
│   ├── ui/                    # Base UI components (buttons, inputs, modals)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── modal.tsx
│   │   ├── toast.tsx
│   │   └── loading.tsx
│   ├── forms/                 # Form components
│   │   ├── agent-form.tsx
│   │   ├── memory-form.tsx
│   │   └── auth-forms.tsx
│   ├── agents/                # Agent-specific components
│   │   ├── agent-builder.tsx  # Drag-and-drop agent builder
│   │   ├── agent-card.tsx     # Agent preview card
│   │   ├── agent-wizard.tsx   # Creation wizard
│   │   └── conversation-simulator.tsx  # Testing interface
│   ├── memory/                # Memory management components
│   │   ├── memory-browser.tsx
│   │   ├── memory-editor.tsx
│   │   └── memory-analytics.tsx
│   ├── knowledge/             # Knowledge base components
│   │   ├── document-uploader.tsx
│   │   ├── knowledge-search.tsx
│   │   └── document-viewer.tsx
│   ├── workflows/             # Workflow design components
│   │   ├── workflow-editor.tsx  # Visual node editor
│   │   ├── workflow-node.tsx
│   │   └── workflow-canvas.tsx
│   └── layout/                # Layout components
│       ├── header.tsx
│       ├── sidebar.tsx
│       ├── navigation.tsx
│       └── footer.tsx
├── lib/                       # Utility libraries
│   ├── api.ts                 # API client with type safety
│   ├── auth.ts                # Authentication utilities
│   ├── types.ts               # TypeScript type definitions
│   ├── utils.ts               # General utilities
│   ├── constants.ts           # Application constants
│   └── env.ts                 # Environment variable validation
├── hooks/                     # Custom React hooks
│   ├── use-api.ts             # API integration hook
│   ├── use-auth.ts            # Authentication hook
│   ├── use-agents.ts          # Agent management hook
│   ├── use-memory.ts          # Memory management hook
│   └── use-knowledge.ts       # Knowledge base hook
├── providers/                 # Context providers
│   ├── auth-provider.tsx      # Authentication context
│   ├── theme-provider.tsx     # Theme/dark mode context
│   └── toast-provider.tsx     # Notification context
├── styles/                    # Additional styling
│   └── components.css         # Component-specific styles
└── __tests__/                 # Frontend tests
    ├── components/            # Component tests
    ├── pages/                 # Page tests
    └── utils/                 # Utility tests
```

### Known Gotchas of our codebase & Library Quirks

```python
# CRITICAL: FastAPI backend requires JWT authentication for most endpoints
# Frontend must include Authorization: Bearer <token> headers
# Authentication flow: POST /auth/login returns JWT token

# CRITICAL: Next.js App Router requirements
# - Server components cannot use browser APIs or React hooks
# - 'use client' directive required for interactive components
# - API routes must export HTTP method functions (GET, POST, etc.)

# CRITICAL: Backend API structure follows domain-driven design
# - Authentication: /auth/login, /auth/register, /auth/me
# - Agents: /agents/ (CRUD operations)
# - Memory: /memory/ (Mem0 integration)
# - Knowledge: /rag/ (R2R integration)
# - Health: /health (system status)

# GOTCHA: Backend uses async/await patterns - frontend API calls must be async
# GOTCHA: Pydantic models use snake_case but frontend typically uses camelCase
# GOTCHA: CORS configuration in backend allows specific origins - verify frontend URL
```

## Implementation Blueprint

### Data Models and Structure

TypeScript interfaces aligned with backend Pydantic models for type safety and consistency.

```typescript
// lib/types.ts - Core type definitions
interface User {
  id: string
  email: string
  created_at: string
  is_active: boolean
}

interface Agent {
  id: string
  name: string
  description: string
  system_prompt: string
  user_id: string
  created_at: string
  updated_at: string
  is_active: boolean
  configuration: Record<string, any>
}

interface Memory {
  id: string
  text: string
  agent_id?: string
  user_id: string
  scope: 'user' | 'agent' | 'session'
  created_at: string
  metadata: Record<string, any>
}

interface KnowledgeBase {
  id: string
  name: string
  description: string
  document_count: number
  created_at: string
  user_id: string
}

interface ApiResponse<T> {
  data: T
  message?: string
  error?: string
}

// Pydantic request models
interface CreateAgentRequest {
  name: string
  description: string
  system_prompt: string
  configuration?: Record<string, any>
}

interface CreateMemoryRequest {
  text: string
  scope: 'user' | 'agent' | 'session'
  agent_id?: string
}
```

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE frontend/package.json and configuration files
  - IMPLEMENT: Next.js 14+ with App Router, TypeScript, Tailwind CSS
  - DEPENDENCIES: next@latest, react, typescript, tailwindcss, @types/react
  - ADDITIONAL: lucide-react (icons), react-hook-form (forms), zod (validation)
  - NAMING: Standard Next.js project structure
  - PLACEMENT: Root of frontend/ directory

Task 2: CREATE frontend/lib/types.ts and frontend/lib/api.ts
  - IMPLEMENT: TypeScript interfaces matching backend Pydantic models
  - FOLLOW pattern: Strict typing with proper error handling
  - NAMING: PascalCase for interfaces, camelCase for functions
  - DEPENDENCIES: Backend API schema from apps/api/app/models/schemas.py
  - PLACEMENT: Utility layer in lib/

Task 3: CREATE frontend/providers/auth-provider.tsx
  - IMPLEMENT: Authentication context with JWT token management
  - FOLLOW pattern: React Context API with TypeScript
  - NAMING: AuthProvider component, useAuth hook
  - DEPENDENCIES: API client from Task 2
  - PLACEMENT: Context providers in providers/

Task 4: CREATE frontend/app/layout.tsx and navigation components
  - IMPLEMENT: Root layout with authentication, navigation, and theming
  - FOLLOW pattern: Next.js App Router layout conventions
  - NAMING: layout.tsx, components in components/layout/
  - DEPENDENCIES: Auth provider from Task 3, UI components
  - PLACEMENT: App Router layout structure

Task 5: CREATE frontend/app/(auth)/login/page.tsx and registration
  - IMPLEMENT: Authentication forms with validation and error handling
  - FOLLOW pattern: React Hook Form with Zod validation
  - NAMING: page.tsx for App Router pages
  - DEPENDENCIES: Auth provider, form components
  - PLACEMENT: Authentication route group in app/(auth)/

Task 6: CREATE frontend/app/(dashboard)/layout.tsx and main pages
  - IMPLEMENT: Dashboard layout with sidebar navigation
  - FOLLOW pattern: Responsive layout with mobile support
  - NAMING: Dashboard route group structure
  - DEPENDENCIES: Authentication, layout components
  - PLACEMENT: Dashboard route group in app/(dashboard)/

Task 7: CREATE frontend/components/agents/agent-builder.tsx
  - IMPLEMENT: Visual agent creation interface with drag-and-drop
  - FOLLOW pattern: React component with state management
  - NAMING: Descriptive component names, PascalCase
  - DEPENDENCIES: Agent types, API client, UI components
  - PLACEMENT: Agent-specific components in components/agents/

Task 8: CREATE frontend/app/(dashboard)/agents/create/page.tsx
  - IMPLEMENT: Agent creation wizard with multi-step form
  - FOLLOW pattern: Next.js App Router page with client components
  - NAMING: App Router page structure
  - DEPENDENCIES: Agent builder component, form validation
  - PLACEMENT: Agent creation page in agents/create/

Task 9: CREATE frontend/components/memory/memory-browser.tsx
  - IMPLEMENT: Memory management interface with search and filtering
  - FOLLOW pattern: Data table with CRUD operations
  - NAMING: Descriptive component names
  - DEPENDENCIES: Memory types, API client, UI components
  - PLACEMENT: Memory-specific components in components/memory/

Task 10: CREATE frontend/components/knowledge/document-uploader.tsx
  - IMPLEMENT: Drag-and-drop file upload with progress tracking
  - FOLLOW pattern: File upload component with validation
  - NAMING: Descriptive component names
  - DEPENDENCIES: Knowledge base types, API client
  - PLACEMENT: Knowledge-specific components in components/knowledge/

Task 11: CREATE frontend/app/(dashboard)/analytics/page.tsx
  - IMPLEMENT: Analytics dashboard with charts and metrics
  - FOLLOW pattern: Dashboard page with data visualization
  - NAMING: App Router page structure
  - DEPENDENCIES: Analytics API, chart components
  - PLACEMENT: Analytics page in dashboard

Task 12: CREATE frontend/__tests__/ test suite
  - IMPLEMENT: Component tests, page tests, and integration tests
  - FOLLOW pattern: Jest + React Testing Library
  - NAMING: test_{component}.tsx naming convention
  - COVERAGE: All major components and user flows
  - PLACEMENT: Tests in __tests__/ directory
```

### Implementation Patterns & Key Details

```typescript
// API client pattern with error handling
// lib/api.ts
class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  setToken(token: string) {
    this.token = token
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options.headers,
    }

    try {
      const response = await fetch(url, { ...options, headers })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      return { data }
    } catch (error) {
      return { 
        data: null as any, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      }
    }
  }

  // Agent management methods
  async getAgents(): Promise<ApiResponse<Agent[]>> {
    return this.request<Agent[]>('/agents/')
  }

  async createAgent(agent: CreateAgentRequest): Promise<ApiResponse<Agent>> {
    return this.request<Agent>('/agents/', {
      method: 'POST',
      body: JSON.stringify(agent),
    })
  }
}

// Authentication provider pattern
// providers/auth-provider.tsx
'use client'

interface AuthContextType {
  user: User | null
  login: (email: string, password: string) => Promise<boolean>
  logout: () => void
  isLoading: boolean
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // PATTERN: Initialize authentication state on mount
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      apiClient.setToken(token)
      // Verify token validity
      apiClient.getProfile().then(response => {
        if (response.data) {
          setUser(response.data)
        } else {
          localStorage.removeItem('auth_token')
        }
        setIsLoading(false)
      })
    } else {
      setIsLoading(false)
    }
  }, [])

  // CRITICAL: Secure token storage and API client configuration
  const login = async (email: string, password: string): Promise<boolean> => {
    const response = await apiClient.login({ email, password })
    if (response.data) {
      localStorage.setItem('auth_token', response.data.token)
      apiClient.setToken(response.data.token)
      setUser(response.data.user)
      return true
    }
    return false
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

// Component pattern with proper TypeScript and accessibility
// components/agents/agent-card.tsx
interface AgentCardProps {
  agent: Agent
  onEdit?: (agent: Agent) => void
  onDelete?: (agent: Agent) => void
  onDeploy?: (agent: Agent) => void
}

export function AgentCard({ agent, onEdit, onDelete, onDeploy }: AgentCardProps) {
  return (
    <div 
      className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
      role="article"
      aria-labelledby={`agent-title-${agent.id}`}
    >
      <h3 
        id={`agent-title-${agent.id}`}
        className="text-lg font-semibold text-gray-900 mb-2"
      >
        {agent.name}
      </h3>
      
      <p className="text-gray-600 mb-4 line-clamp-2">
        {agent.description}
      </p>
      
      <div className="flex items-center justify-between">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          agent.is_active 
            ? 'bg-green-100 text-green-800' 
            : 'bg-gray-100 text-gray-800'
        }`}>
          {agent.is_active ? 'Active' : 'Inactive'}
        </span>
        
        <div className="flex space-x-2">
          {onEdit && (
            <button
              onClick={() => onEdit(agent)}
              className="text-blue-600 hover:text-blue-800"
              aria-label={`Edit ${agent.name}`}
            >
              Edit
            </button>
          )}
          {onDeploy && (
            <button
              onClick={() => onDeploy(agent)}
              className="text-green-600 hover:text-green-800"
              aria-label={`Deploy ${agent.name}`}
            >
              Deploy
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
```

### Integration Points

```yaml
BACKEND_API:
  - authentication: "POST /auth/login for JWT token"
  - agents: "CRUD operations at /agents/ endpoint"
  - memory: "Memory operations at /memory/ endpoint"
  - knowledge: "Document operations at /rag/ endpoint"

CONFIGURATION:
  - add to: frontend/next.config.js
  - pattern: "API proxy configuration to backend"
  - cors: "Verify CORS allows frontend origin"

DEPLOYMENT:
  - add to: docker-compose.yml
  - pattern: "Frontend service with nginx or Next.js standalone"
  - env_vars: "NEXT_PUBLIC_API_URL for backend connection"

TESTING:
  - integration: "Jest + React Testing Library"
  - e2e: "Playwright for critical user journeys"
  - accessibility: "axe-core for WCAG compliance testing"
```

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Run after each file creation - fix before proceeding
cd frontend/
npm run lint   # Biome linting
npm run format # optional formatting

# Expected: Zero errors. If errors exist, READ output and fix before proceeding.
```

### Level 2: Unit Tests (Component Validation)

```bash
# Test each component as it's created
cd frontend/
npm run test components/agents/agent-card.test.tsx
npm run test components/memory/memory-browser.test.tsx

# Full test suite for affected areas
npm run test components/ 
npm run test pages/

# Coverage validation
npm run test:coverage

# Expected: All tests pass. If failing, debug root cause and fix implementation.
```

### Level 3: Integration Testing (System Validation)

```bash
# Start backend services first
cd .. && docker compose up -d
cd apps/api && uvicorn app.main:app --reload &

# Start frontend development server
cd frontend/
npm run dev &
sleep 5  # Allow startup time

# Health check validation
curl -f http://localhost:3000/ || echo "Frontend health check failed"
curl -f http://localhost:8000/health || echo "Backend health check failed"

# Authentication flow testing
# Test login/logout flow through UI
npm run test:e2e auth.spec.ts

# Agent creation flow testing
npm run test:e2e agent-creation.spec.ts

# API integration validation
# Verify frontend can communicate with backend
npm run test:integration

# Expected: All integrations working, proper responses, no connection errors
```

### Level 4: Creative & Domain-Specific Validation

```bash
# User Experience Validation
npm run test:e2e user-journey.spec.ts

# Accessibility Testing
npm run test:accessibility

# Performance Testing
npm run build
npm run start &
lighthouse http://localhost:3000 --output=json --output-path=./lighthouse-report.json

# Mobile Responsiveness
npm run test:responsive

# Browser Compatibility
npm run test:cross-browser

# Agent Creation Speed Test (must be <5 minutes per PRD)
npm run test:e2e agent-creation-speed.spec.ts

# Security Testing
npm run test:security

# Expected: All creative validations pass, performance meets requirements
```

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] All tests pass: `npm run test`
- [ ] No TypeScript errors: `npm run type-check`
- [ ] No Biome linting errors: `npm run lint`
- [ ] Production build successful: `npm run build`
- [ ] Frontend-backend integration working: API calls succeed

### Feature Validation

- [ ] All success criteria from "What" section met
- [ ] Dashboard loads in <2 seconds (per requirements)
- [ ] Agent creation wizard completes in <5 minutes
- [ ] Memory management interface provides real-time functionality
- [ ] Knowledge base upload supports drag-and-drop with progress
- [ ] Testing interface provides conversation simulation
- [ ] User authentication and registration flows work correctly
- [ ] Mobile responsive design works on tablets (>768px)

### Code Quality Validation

- [ ] Follows Next.js App Router best practices
- [ ] TypeScript strict mode enabled with no any types
- [ ] Components follow accessibility guidelines (WCAG 2.1 AA)
- [ ] API integration uses proper error handling
- [ ] Authentication flow is secure with JWT token management
- [ ] File placement matches desired codebase tree structure

### Documentation & Deployment

- [ ] Component interfaces clearly defined and documented
- [ ] Environment variables properly configured
- [ ] API endpoints properly proxied through Next.js
- [ ] Docker integration configured for deployment
- [ ] Error logging provides useful debugging information

---

## Anti-Patterns to Avoid

- ❌ Don't use Pages Router patterns in App Router project
- ❌ Don't access window/browser APIs in server components
- ❌ Don't skip TypeScript type checking in production builds
- ❌ Don't hardcode API URLs - use environment variables
- ❌ Don't ignore accessibility requirements for enterprise users
- ❌ Don't skip error handling in API integration
- ❌ Don't use 'use client' directive unless component needs browser APIs
- ❌ Don't mix authentication state between server and client components


---

# AGENTS.md: Next.js Frontend Collaboration Guide

<!-- This file provides specialized guidance for AI agents working on the AgentFlow Next.js + TypeScript frontend. It supplements the root AGENTS.md with frontend-specific requirements. -->

## Component Scope

This AGENTS.md covers the Next.js + TypeScript frontend application for AgentFlow, which provides the user interface for agent creation, memory management, workflow design, knowledge base management, and platform analytics. This component implements the App Router architecture with server and client components.

**Note:** This frontend component is planned but not yet implemented in the current codebase. This guide provides the framework for when frontend development begins.

## Next.js App Router Architecture

### Project Structure Pattern
```
frontend/
├── app/                    # App Router directory
│   ├── layout.tsx         # Root layout component
│   ├── page.tsx           # Home page
│   ├── globals.css        # Global styles
│   ├── (dashboard)/       # Route group for dashboard
│   │   ├── layout.tsx     # Dashboard layout
│   │   ├── agents/        # Agent management pages
│   │   ├── memory/        # Memory management pages
│   │   ├── knowledge/     # Knowledge base pages
│   │   └── analytics/     # Analytics and monitoring
│   ├── api/              # API route handlers
│   │   ├── auth/         # Authentication endpoints
│   │   └── proxy/        # API proxy to backend
│   └── (auth)/           # Authentication pages
│       ├── login/
│       └── register/
├── components/            # Reusable UI components
│   ├── ui/               # Base UI components
│   ├── forms/            # Form components
│   ├── agents/           # Agent-specific components
│   ├── memory/           # Memory management components
│   └── knowledge/        # Knowledge base components
├── lib/                  # Utility libraries
│   ├── api.ts           # API client
│   ├── auth.ts          # Authentication utilities
│   ├── types.ts         # TypeScript type definitions
│   └── utils.ts         # General utilities
├── hooks/               # Custom React hooks
├── providers/           # Context providers
└── styles/             # Additional styling
```

### TypeScript Configuration
```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "skipLibCheck": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictPropertyInitialization": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"],
      "@/components/*": ["./components/*"],
      "@/lib/*": ["./lib/*"],
      "@/hooks/*": ["./hooks/*"],
      "@/types/*": ["./lib/types/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

## Component Architecture Patterns

### Server vs Client Component Strategy
```typescript
// Server Component for data fetching (default)
// app/agents/page.tsx
import { getAgents } from '@/lib/api'
import { AgentsList } from '@/components/agents/AgentsList'

export default async function AgentsPage() {
  // Fetch data on server - no loading state needed
  const agents = await getAgents()
  
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">AI Agents</h1>
      <AgentsList agents={agents} />
    </div>
  )
}

// Client Component for interactivity
// components/agents/AgentsList.tsx
'use client'

import { useState } from 'react'
import { Agent } from '@/lib/types'
import { AgentCard } from './AgentCard'

interface AgentsListProps {
  agents: Agent[]
}

export function AgentsList({ agents }: AgentsListProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  
  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = !selectedCategory || agent.category === selectedCategory
    return matchesSearch && matchesCategory
  })
  
  return (
    <div>
      {/* Search and filter controls */}
      <div className="mb-6 space-y-4">
        <input
          type="text"
          placeholder="Search agents..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {/* Category filter */}
      </div>
      
      {/* Agent grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map(agent => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  )
}
```

### Data Fetching Patterns
```typescript
// lib/api.ts - API client with proper error handling
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'APIError'
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  
  // Get auth token from cookies or session
  const token = await getAuthToken()
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  }
  
  try {
    const response = await fetch(url, config)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        response.status,
        errorData.detail || `HTTP ${response.status}`
      )
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    throw new APIError(500, 'Network error')
  }
}

// Agent API functions
export async function getAgents(): Promise<Agent[]> {
  return apiRequest<Agent[]>('/agents/')
}

export async function createAgent(agentData: CreateAgentRequest): Promise<Agent> {
  return apiRequest<Agent>('/agents/', {
    method: 'POST',
    body: JSON.stringify(agentData),
  })
}

export async function updateAgent(id: string, updates: Partial<Agent>): Promise<Agent> {
  return apiRequest<Agent>(`/agents/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  })
}

// Memory API functions
export async function searchMemories(query: string, limit = 10): Promise<Memory[]> {
  const params = new URLSearchParams({ q: query, limit: limit.toString() })
  return apiRequest<Memory[]>(`/memory/search?${params}`)
}

export async function createMemory(memoryData: CreateMemoryRequest): Promise<Memory> {
  return apiRequest<Memory>('/memory/', {
    method: 'POST',
    body: JSON.stringify(memoryData),
  })
}

// Real-time updates with Server-Sent Events
export function createEventStream(endpoint: string): EventSource {
  const token = getAuthTokenSync() // Synchronous version for EventSource
  const url = `${API_BASE_URL}${endpoint}?token=${encodeURIComponent(token)}`
  return new EventSource(url)
}
```

### Type-Safe Form Handling
```typescript
// lib/types.ts - Comprehensive type definitions
export interface Agent {
  id: string
  name: string
  description: string
  category: AgentCategory
  status: AgentStatus
  created_at: string
  updated_at: string
  config: AgentConfig
  metrics?: AgentMetrics
}

export interface AgentConfig {
  system_prompt: string
  model: string
  temperature: number
  max_tokens: number
  tools: string[]
  memory_scope: MemoryScope
}

export interface CreateAgentRequest {
  name: string
  description: string
  category: AgentCategory
  config: Partial<AgentConfig>
}

export type AgentCategory = 'customer_support' | 'research' | 'data_analysis' | 'content' | 'custom'
export type AgentStatus = 'draft' | 'active' | 'paused' | 'archived'
export type MemoryScope = 'user' | 'agent' | 'session' | 'global'

// Form validation with Zod
import { z } from 'zod'

export const CreateAgentSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name too long'),
  description: z.string().min(10, 'Description must be at least 10 characters').max(500),
  category: z.enum(['customer_support', 'research', 'data_analysis', 'content', 'custom']),
  config: z.object({
    system_prompt: z.string().min(1, 'System prompt is required'),
    model: z.string().default('gpt-4o-mini'),
    temperature: z.number().min(0).max(2).default(0.7),
    max_tokens: z.number().min(1).max(4000).default(1000),
    tools: z.array(z.string()).default([]),
    memory_scope: z.enum(['user', 'agent', 'session', 'global']).default('user')
  })
})

export type CreateAgentFormData = z.infer<typeof CreateAgentSchema>

// Form component with validation
// components/agents/CreateAgentForm.tsx
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { CreateAgentSchema, type CreateAgentFormData } from '@/lib/types'
import { createAgent } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'

export function CreateAgentForm() {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const form = useForm<CreateAgentFormData>({
    resolver: zodResolver(CreateAgentSchema),
    defaultValues: {
      name: '',
      description: '',
      category: 'custom',
      config: {
        system_prompt: '',
        model: 'gpt-4o-mini',
        temperature: 0.7,
        max_tokens: 1000,
        tools: [],
        memory_scope: 'user'
      }
    }
  })
  
  const onSubmit = async (data: CreateAgentFormData) => {
    setIsSubmitting(true)
    try {
      const agent = await createAgent(data)
      router.push(`/agents/${agent.id}`)
    } catch (error) {
      console.error('Failed to create agent:', error)
      // Show error toast or set form error
    } finally {
      setIsSubmitting(false)
    }
  }
  
  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <label htmlFor="name" className="block text-sm font-medium mb-2">
          Agent Name
        </label>
        <Input
          id="name"
          {...form.register('name')}
          placeholder="Enter agent name"
          error={form.formState.errors.name?.message}
        />
      </div>
      
      <div>
        <label htmlFor="description" className="block text-sm font-medium mb-2">
          Description
        </label>
        <Textarea
          id="description"
          {...form.register('description')}
          placeholder="Describe what this agent does"
          rows={3}
          error={form.formState.errors.description?.message}
        />
      </div>
      
      <div>
        <label htmlFor="category" className="block text-sm font-medium mb-2">
          Category
        </label>
        <Select
          id="category"
          {...form.register('category')}
          options={[
            { value: 'customer_support', label: 'Customer Support' },
            { value: 'research', label: 'Research Assistant' },
            { value: 'data_analysis', label: 'Data Analysis' },
            { value: 'content', label: 'Content Creation' },
            { value: 'custom', label: 'Custom' }
          ]}
        />
      </div>
      
      <div>
        <label htmlFor="system_prompt" className="block text-sm font-medium mb-2">
          System Prompt
        </label>
        <Textarea
          id="system_prompt"
          {...form.register('config.system_prompt')}
          placeholder="Define the agent's behavior and personality"
          rows={5}
          error={form.formState.errors.config?.system_prompt?.message}
        />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="temperature" className="block text-sm font-medium mb-2">
            Temperature
          </label>
          <Input
            id="temperature"
            type="number"
            step="0.1"
            min="0"
            max="2"
            {...form.register('config.temperature', { valueAsNumber: true })}
          />
        </div>
        
        <div>
          <label htmlFor="max_tokens" className="block text-sm font-medium mb-2">
            Max Tokens
          </label>
          <Input
            id="max_tokens"
            type="number"
            min="1"
            max="4000"
            {...form.register('config.max_tokens', { valueAsNumber: true })}
          />
        </div>
      </div>
      
      <Button
        type="submit"
        disabled={isSubmitting}
        className="w-full"
      >
        {isSubmitting ? 'Creating Agent...' : 'Create Agent'}
      </Button>
    </form>
  )
}
```

### State Management with Context
```typescript
// providers/AgentProvider.tsx
'use client'

import { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import { Agent } from '@/lib/types'
import { getAgents } from '@/lib/api'

interface AgentState {
  agents: Agent[]
  selectedAgent: Agent | null
  loading: boolean
  error: string | null
}

type AgentAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_AGENTS'; payload: Agent[] }
  | { type: 'SET_SELECTED_AGENT'; payload: Agent | null }
  | { type: 'ADD_AGENT'; payload: Agent }
  | { type: 'UPDATE_AGENT'; payload: Agent }
  | { type: 'DELETE_AGENT'; payload: string }
  | { type: 'SET_ERROR'; payload: string | null }

const agentReducer = (state: AgentState, action: AgentAction): AgentState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload }
    case 'SET_AGENTS':
      return { ...state, agents: action.payload, loading: false, error: null }
    case 'SET_SELECTED_AGENT':
      return { ...state, selectedAgent: action.payload }
    case 'ADD_AGENT':
      return { ...state, agents: [...state.agents, action.payload] }
    case 'UPDATE_AGENT':
      return {
        ...state,
        agents: state.agents.map(agent =>
          agent.id === action.payload.id ? action.payload : agent
        ),
        selectedAgent: state.selectedAgent?.id === action.payload.id
          ? action.payload
          : state.selectedAgent
      }
    case 'DELETE_AGENT':
      return {
        ...state,
        agents: state.agents.filter(agent => agent.id !== action.payload),
        selectedAgent: state.selectedAgent?.id === action.payload
          ? null
          : state.selectedAgent
      }
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false }
    default:
      return state
  }
}

const AgentContext = createContext<{
  state: AgentState
  dispatch: React.Dispatch<AgentAction>
} | null>(null)

export function AgentProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(agentReducer, {
    agents: [],
    selectedAgent: null,
    loading: true,
    error: null
  })
  
  useEffect(() => {
    const loadAgents = async () => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true })
        const agents = await getAgents()
        dispatch({ type: 'SET_AGENTS', payload: agents })
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: 'Failed to load agents' })
      }
    }
    
    loadAgents()
  }, [])
  
  return (
    <AgentContext.Provider value={{ state, dispatch }}>
      {children}
    </AgentContext.Provider>
  )
}

export function useAgents() {
  const context = useContext(AgentContext)
  if (!context) {
    throw new Error('useAgents must be used within an AgentProvider')
  }
  return context
}
```

## Real-Time Features and WebSocket Integration

### Real-Time Agent Execution
```typescript
// hooks/useAgentExecution.ts
'use client'

import { useState, useEffect, useCallback } from 'react'
import { createEventStream } from '@/lib/api'

interface AgentExecutionState {
  status: 'idle' | 'running' | 'completed' | 'error'
  messages: AgentMessage[]
  error: string | null
}

interface AgentMessage {
  id: string
  type: 'user' | 'agent' | 'system'
  content: string
  timestamp: string
  metadata?: Record<string, any>
}

export function useAgentExecution(agentId: string) {
  const [state, setState] = useState<AgentExecutionState>({
    status: 'idle',
    messages: [],
    error: null
  })
  
  const sendMessage = useCallback(async (content: string) => {
    setState(prev => ({
      ...prev,
      status: 'running',
      messages: [
        ...prev.messages,
        {
          id: crypto.randomUUID(),
          type: 'user',
          content,
          timestamp: new Date().toISOString()
        }
      ]
    }))
    
    try {
      // Create EventSource for streaming response
      const eventSource = createEventStream(`/agents/${agentId}/execute`)
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        setState(prev => ({
          ...prev,
          messages: [
            ...prev.messages,
            {
              id: data.id,
              type: 'agent',
              content: data.content,
              timestamp: data.timestamp,
              metadata: data.metadata
            }
          ]
        }))
      }
      
      eventSource.addEventListener('done', () => {
        setState(prev => ({ ...prev, status: 'completed' }))
        eventSource.close()
      })
      
      eventSource.onerror = () => {
        setState(prev => ({
          ...prev,
          status: 'error',
          error: 'Connection lost'
        }))
        eventSource.close()
      }
      
      // Send initial message
      await fetch(`/api/agents/${agentId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content })
      })
      
    } catch (error) {
      setState(prev => ({
        ...prev,
        status: 'error',
        error: 'Failed to send message'
      }))
    }
  }, [agentId])
  
  const reset = useCallback(() => {
    setState({
      status: 'idle',
      messages: [],
      error: null
    })
  }, [])
  
  return {
    ...state,
    sendMessage,
    reset
  }
}

// components/agents/AgentChat.tsx
'use client'

import { useState } from 'react'
import { useAgentExecution } from '@/hooks/useAgentExecution'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { MessageList } from './MessageList'

interface AgentChatProps {
  agentId: string
}

export function AgentChat({ agentId }: AgentChatProps) {
  const [input, setInput] = useState('')
  const { status, messages, error, sendMessage, reset } = useAgentExecution(agentId)
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || status === 'running') return
    
    await sendMessage(input)
    setInput('')
  }
  
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList messages={messages} />
        {error && (
          <div className="text-red-500 text-sm mt-2">
            Error: {error}
          </div>
        )}
      </div>
      
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={status === 'running'}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!input.trim() || status === 'running'}
          >
            {status === 'running' ? 'Sending...' : 'Send'}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={reset}
            disabled={status === 'running'}
          >
            Reset
          </Button>
        </div>
      </form>
    </div>
  )
}
```

## Visual Workflow Editor

### Workflow Canvas Component
```typescript
// components/workflows/WorkflowCanvas.tsx
'use client'

import { useState, useCallback, useRef } from 'react'
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  ReactFlowProvider,
} from 'reactflow'
import 'reactflow/dist/style.css'

import { WorkflowNode } from './WorkflowNode'
import { NodePalette } from './NodePalette'

const nodeTypes = {
  workflow: WorkflowNode,
}

interface WorkflowCanvasProps {
  workflowId?: string
  initialNodes?: Node[]
  initialEdges?: Edge[]
  onSave?: (nodes: Node[], edges: Edge[]) => void
}

export function WorkflowCanvas({
  workflowId,
  initialNodes = [],
  initialEdges = [],
  onSave
}: WorkflowCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [isValidating, setIsValidating] = useState(false)
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge(params, eds))
    },
    [setEdges]
  )
  
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])
  
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      
      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect()
      const type = event.dataTransfer.getData('application/reactflow')
      
      if (typeof type === 'undefined' || !type || !reactFlowBounds) {
        return
      }
      
      const position = {
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      }
      
      const newNode: Node = {
        id: crypto.randomUUID(),
        type: 'workflow',
        position,
        data: { 
          label: `${type} node`,
          nodeType: type,
          config: getDefaultNodeConfig(type)
        },
      }
      
      setNodes((nds) => nds.concat(newNode))
    },
    [setNodes]
  )
  
  const validateWorkflow = useCallback(async () => {
    setIsValidating(true)
    try {
      // Validate workflow structure
      const validation = await validateWorkflowStructure(nodes, edges)
      
      if (!validation.isValid) {
        // Show validation errors
        console.error('Workflow validation failed:', validation.errors)
        return false
      }
      
      return true
    } catch (error) {
      console.error('Validation error:', error)
      return false
    } finally {
      setIsValidating(false)
    }
  }, [nodes, edges])
  
  const handleSave = useCallback(async () => {
    const isValid = await validateWorkflow()
    if (isValid && onSave) {
      onSave(nodes, edges)
    }
  }, [nodes, edges, validateWorkflow, onSave])
  
  return (
    <div className="flex h-full">
      <NodePalette />
      
      <div className="flex-1" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      </div>
      
      <div className="w-80 bg-gray-50 p-4 border-l">
        <div className="space-y-4">
          <Button
            onClick={handleSave}
            disabled={isValidating}
            className="w-full"
          >
            {isValidating ? 'Validating...' : 'Save Workflow'}
          </Button>
          
          <Button
            onClick={validateWorkflow}
            variant="outline"
            className="w-full"
          >
            Validate Workflow
          </Button>
        </div>
      </div>
    </div>
  )
}

// Helper functions
function getDefaultNodeConfig(nodeType: string) {
  switch (nodeType) {
    case 'agent':
      return { agentId: '', prompt: '' }
    case 'memory':
      return { operation: 'search', query: '' }
    case 'condition':
      return { condition: '', trueLabel: 'Yes', falseLabel: 'No' }
    default:
      return {}
  }
}

async function validateWorkflowStructure(nodes: Node[], edges: Edge[]) {
  const errors: string[] = []
  
  // Check for at least one start node
  const startNodes = nodes.filter(node => node.data.nodeType === 'start')
  if (startNodes.length === 0) {
    errors.push('Workflow must have at least one start node')
  }
  
  // Check for disconnected nodes
  const connectedNodeIds = new Set([
    ...edges.map(edge => edge.source),
    ...edges.map(edge => edge.target)
  ])
  
  const disconnectedNodes = nodes.filter(node => 
    node.data.nodeType !== 'start' && !connectedNodeIds.has(node.id)
  )
  
  if (disconnectedNodes.length > 0) {
    errors.push(`Found ${disconnectedNodes.length} disconnected nodes`)
  }
  
  // Check for cycles (if not allowed)
  const hasCycles = detectCycles(nodes, edges)
  if (hasCycles) {
    errors.push('Workflow contains cycles')
  }
  
  return {
    isValid: errors.length === 0,
    errors
  }
}

function detectCycles(nodes: Node[], edges: Edge[]): boolean {
  // Simple cycle detection using DFS
  const graph = new Map<string, string[]>()
  
  // Build adjacency list
  nodes.forEach(node => graph.set(node.id, []))
  edges.forEach(edge => {
    const neighbors = graph.get(edge.source) || []
    neighbors.push(edge.target)
    graph.set(edge.source, neighbors)
  })
  
  const visited = new Set<string>()
  const recursionStack = new Set<string>()
  
  function dfs(nodeId: string): boolean {
    visited.add(nodeId)
    recursionStack.add(nodeId)
    
    const neighbors = graph.get(nodeId) || []
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        if (dfs(neighbor)) return true
      } else if (recursionStack.has(neighbor)) {
        return true // Cycle detected
      }
    }
    
    recursionStack.delete(nodeId)
    return false
  }
  
  for (const node of nodes) {
    if (!visited.has(node.id)) {
      if (dfs(node.id)) return true
    }
  }
  
  return false
}
```

## Authentication and Security

### JWT Authentication Hook
```typescript
// hooks/useAuth.ts
'use client'

import { useState, useEffect, createContext, useContext, ReactNode } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  id: string
  email: string
  name: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    loading: true
  })
  const router = useRouter()
  
  useEffect(() => {
    // Check for existing token on mount
    const token = localStorage.getItem('agentflow_token')
    if (token) {
      validateToken(token)
    } else {
      setState(prev => ({ ...prev, loading: false }))
    }
  }, [])
  
  const validateToken = async (token: string) => {
    try {
      const response = await fetch('/api/auth/validate', {
        headers: { Authorization: `Bearer ${token}` }
      })
      
      if (response.ok) {
        const user = await response.json()
        setState({ user, token, loading: false })
      } else {
        localStorage.removeItem('agentflow_token')
        setState({ user: null, token: null, loading: false })
      }
    } catch (error) {
      localStorage.removeItem('agentflow_token')
      setState({ user: null, token: null, loading: false })
    }
  }
  
  const login = async (email: string, password: string) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }
    
    const { user, token } = await response.json()
    localStorage.setItem('agentflow_token', token)
    setState({ user, token, loading: false })
    router.push('/dashboard')
  }
  
  const logout = () => {
    localStorage.removeItem('agentflow_token')
    setState({ user: null, token: null, loading: false })
    router.push('/login')
  }
  
  const refreshToken = async () => {
    const currentToken = state.token
    if (!currentToken) return
    
    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { Authorization: `Bearer ${currentToken}` }
      })
      
      if (response.ok) {
        const { token: newToken } = await response.json()
        localStorage.setItem('agentflow_token', newToken)
        setState(prev => ({ ...prev, token: newToken }))
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
    }
  }
  
  return (
    <AuthContext.Provider value={{ ...state, login, logout, refreshToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Route protection component
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const router = useRouter()
  
  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])
  
  if (loading) {
    return <div>Loading...</div>
  }
  
  if (!user) {
    return null
  }
  
  return <>{children}</>
}
```

## Performance Optimization

### Code Splitting and Lazy Loading
```typescript
// Lazy load heavy components
import dynamic from 'next/dynamic'

const WorkflowCanvas = dynamic(
  () => import('@/components/workflows/WorkflowCanvas'),
  {
    loading: () => <div>Loading workflow editor...</div>,
    ssr: false // Disable SSR for client-only components
  }
)

const AgentAnalytics = dynamic(
  () => import('@/components/agents/AgentAnalytics'),
  {
    loading: () => <div>Loading analytics...</div>
  }
)

// Optimize image loading
import Image from 'next/image'

export function AgentCard({ agent }: { agent: Agent }) {
  return (
    <div className="card">
      <Image
        src={agent.avatar || '/default-agent.png'}
        alt={agent.name}
        width={64}
        height={64}
        priority={false} // Only set true for above-fold images
        placeholder="blur"
        blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
      />
      {/* Rest of card content */}
    </div>
  )
}
```

## Testing Patterns

### Component Testing with React Testing Library
```typescript
// components/__tests__/AgentCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { AgentCard } from '../agents/AgentCard'
import { Agent } from '@/lib/types'

const mockAgent: Agent = {
  id: '1',
  name: 'Test Agent',
  description: 'A test agent for testing',
  category: 'custom',
  status: 'active',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  config: {
    system_prompt: 'You are a helpful assistant',
    model: 'gpt-4o-mini',
    temperature: 0.7,
    max_tokens: 1000,
    tools: [],
    memory_scope: 'user'
  }
}

describe('AgentCard', () => {
  it('renders agent information correctly', () => {
    render(<AgentCard agent={mockAgent} />)
    
    expect(screen.getByText('Test Agent')).toBeInTheDocument()
    expect(screen.getByText('A test agent for testing')).toBeInTheDocument()
    expect(screen.getByText('Custom')).toBeInTheDocument()
  })
  
  it('handles click events', () => {
    const onSelect = jest.fn()
    render(<AgentCard agent={mockAgent} onSelect={onSelect} />)
    
    fireEvent.click(screen.getByRole('button'))
    expect(onSelect).toHaveBeenCalledWith(mockAgent)
  })
  
  it('shows correct status badge', () => {
    render(<AgentCard agent={mockAgent} />)
    
    const statusBadge = screen.getByText('Active')
    expect(statusBadge).toHaveClass('bg-green-100', 'text-green-800')
  })
})

// API testing with MSW (Mock Service Worker)
// __tests__/setup.ts
import { setupServer } from 'msw/node'
import { rest } from 'msw'

export const server = setupServer(
  rest.get('/api/agents', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: '1',
          name: 'Test Agent',
          description: 'Test description',
          category: 'custom',
          status: 'active',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
          config: {
            system_prompt: 'Test prompt',
            model: 'gpt-4o-mini',
            temperature: 0.7,
            max_tokens: 1000,
            tools: [],
            memory_scope: 'user'
          }
        }
      ])
    )
  }),
  
  rest.post('/api/agents', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: '2',
        ...req.body,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      })
    )
  }),
  
  rest.get('/api/memory/search', (req, res, ctx) => {
    const query = req.url.searchParams.get('q')
    return res(
      ctx.json([
        {
          id: '1',
          text: `Memory related to ${query}`,
          scope: 'user',
          created_at: '2025-01-01T00:00:00Z',
          metadata: {}
        }
      ])
    )
  })
)

// Integration testing for hooks
// hooks/__tests__/useAgents.test.tsx
import { renderHook, waitFor } from '@testing-library/react'
import { useAgents, AgentProvider } from '@/providers/AgentProvider'
import { server } from '../setup'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('useAgents', () => {
  it('loads agents on mount', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AgentProvider>{children}</AgentProvider>
    )
    
    const { result } = renderHook(() => useAgents(), { wrapper })
    
    expect(result.current.state.loading).toBe(true)
    
    await waitFor(() => {
      expect(result.current.state.loading).toBe(false)
    })
    
    expect(result.current.state.agents).toHaveLength(1)
    expect(result.current.state.agents[0].name).toBe('Test Agent')
  })
})
```

## Development Workflow

### Local Development Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run type checking
npm run type-check

# Run linting
npm run lint
npm run lint:fix

# Run tests
npm run test
npm run test:watch
npm run test:coverage

# Build for production
npm run build

# Preview production build
npm start
```

### Package.json Scripts
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "biome check .",
    "lint:fix": "biome check . --apply",
    "type-check": "tsc --noEmit",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "build-analyze": "ANALYZE=true npm run build",
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build"
  }
}
```

### Environment Configuration
```typescript
// lib/env.ts - Type-safe environment variables
import { z } from 'zod'

const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url(),
  NEXT_PUBLIC_APP_ENV: z.enum(['development', 'staging', 'production']).default('development'),
  NEXT_PUBLIC_SENTRY_DSN: z.string().optional(),
  NEXT_PUBLIC_ANALYTICS_ID: z.string().optional(),
})

export const env = envSchema.parse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_APP_ENV: process.env.NEXT_PUBLIC_APP_ENV,
  NEXT_PUBLIC_SENTRY_DSN: process.env.NEXT_PUBLIC_SENTRY_DSN,
  NEXT_PUBLIC_ANALYTICS_ID: process.env.NEXT_PUBLIC_ANALYTICS_ID,
})

// Validate environment variables at build time
export function validateEnv() {
  try {
    envSchema.parse(process.env)
    console.log('✅ Environment variables are valid')
  } catch (error) {
    console.error('❌ Invalid environment variables:')
    console.error(error)
    process.exit(1)
  }
}
```

## Accessibility and UX Guidelines

### WCAG 2.1 AA Compliance
```typescript
// components/ui/Button.tsx - Accessible button component
import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center rounded-md font-medium transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2',
          'disabled:pointer-events-none disabled:opacity-50',
          
          // Variants
          {
            'bg-blue-600 text-white hover:bg-blue-700': variant === 'primary',
            'bg-gray-200 text-gray-900 hover:bg-gray-300': variant === 'secondary',
            'border border-gray-300 bg-transparent hover:bg-gray-50': variant === 'outline',
            'hover:bg-gray-100': variant === 'ghost',
          },
          
          // Sizes
          {
            'h-8 px-3 text-sm': size === 'sm',
            'h-10 px-4': size === 'md',
            'h-12 px-6 text-lg': size === 'lg',
          },
          
          className
        )}
        disabled={disabled || loading}
        aria-busy={loading}
        {...props}
      >
        {loading ? (
          <>
            <svg
              className="mr-2 h-4 w-4 animate-spin"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span className="sr-only">Loading...</span>
          </>
        ) : null}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
```

### Keyboard Navigation Support
```typescript
// hooks/useKeyboardNavigation.ts
import { useEffect, useCallback } from 'react'

interface UseKeyboardNavigationProps {
  onEscape?: () => void
  onEnter?: () => void
  onArrowUp?: () => void
  onArrowDown?: () => void
  onArrowLeft?: () => void
  onArrowRight?: () => void
  enabled?: boolean
}

export function useKeyboardNavigation({
  onEscape,
  onEnter,
  onArrowUp,
  onArrowDown,
  onArrowLeft,
  onArrowRight,
  enabled = true
}: UseKeyboardNavigationProps) {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return
    
    switch (event.key) {
      case 'Escape':
        onEscape?.()
        break
      case 'Enter':
        onEnter?.()
        break
      case 'ArrowUp':
        event.preventDefault()
        onArrowUp?.()
        break
      case 'ArrowDown':
        event.preventDefault()
        onArrowDown?.()
        break
      case 'ArrowLeft':
        onArrowLeft?.()
        break
      case 'ArrowRight':
        onArrowRight?.()
        break
    }
  }, [enabled, onEscape, onEnter, onArrowUp, onArrowDown, onArrowLeft, onArrowRight])
  
  useEffect(() => {
    if (enabled) {
      document.addEventListener('keydown', handleKeyDown)
      return () => document.removeEventListener('keydown', handleKeyDown)
    }
  }, [enabled, handleKeyDown])
}

// Usage in modal component
export function Modal({ isOpen, onClose, children }: ModalProps) {
  useKeyboardNavigation({
    onEscape: onClose,
    enabled: isOpen
  })
  
  // Focus trap implementation
  useEffect(() => {
    if (isOpen) {
      const previousActiveElement = document.activeElement as HTMLElement
      
      // Focus first interactive element in modal
      const firstFocusable = document.querySelector(
        '[role="dialog"] button, [role="dialog"] [href], [role="dialog"] input, [role="dialog"] select, [role="dialog"] textarea, [role="dialog"] [tabindex]:not([tabindex="-1"])'
      ) as HTMLElement
      
      firstFocusable?.focus()
      
      return () => {
        previousActiveElement?.focus()
      }
    }
  }, [isOpen])
  
  if (!isOpen) return null
  
  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
    >
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        {children}
      </div>
    </div>
  )
}
```

## Critical Frontend Development Rules

### Next.js App Router Rules
- **NEVER** use Pages Router patterns in App Router projects
- **NEVER** use `getServerSideProps` or `getStaticProps` - use server components instead
- **NEVER** access `window` or browser APIs in server components
- **NEVER** use `'use client'` unless you need browser APIs or React hooks
- **NEVER** mix App Router and Pages Router in the same project

### TypeScript Rules
- **NEVER** use `any` type - always use proper typing
- **NEVER** ignore TypeScript errors with `@ts-ignore` or `@ts-expect-error`
- **NEVER** skip type checking in CI/CD pipelines
- **NEVER** use `as any` for type assertions
- **NEVER** disable strict mode or strict TypeScript options

### Performance Rules
- **NEVER** import entire libraries when you only need specific functions
- **NEVER** skip image optimization - always use `next/image`
- **NEVER** block the main thread with heavy computations
- **NEVER** fetch data in client components when server components can do it
- **NEVER** skip lazy loading for heavy components

### Security Rules
- **NEVER** expose API keys or secrets in client-side code
- **NEVER** trust user input without validation
- **NEVER** skip CSRF protection for state-changing operations
- **NEVER** use `dangerouslySetInnerHTML` without sanitization
- **NEVER** skip authentication checks in protected routes

### Accessibility Rules
- **NEVER** remove focus indicators without providing alternatives
- **NEVER** use color alone to convey information
- **NEVER** skip alt text for images
- **NEVER** create keyboard traps without proper escape mechanisms
- **NEVER** ignore screen reader support for dynamic content

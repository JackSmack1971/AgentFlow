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
npm run type-check              # TypeScript validation
npm run lint                    # ESLint + Next.js linting
npm run build                   # Next.js build validation

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
- [ ] No linting errors: `npm run lint`
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

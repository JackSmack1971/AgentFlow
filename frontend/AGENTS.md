# AGENTS.md: Next.js Frontend Guidelines

This document provides specific guidance for AI models working with the AgentFlow Next.js frontend located in `/frontend/`. These guidelines are derived from the Next.js+TypeScript, TypeScript 5.x, React 18, and Biome linter rulesets.

## 1. Project Scope & Architecture
*   **Primary Purpose:** Next.js 14+ App Router frontend with component-based architecture for AgentFlow platform
*   **Core Technologies:** Next.js 14+, React 18+, TypeScript 5.x, Tailwind CSS, Biome (linting/formatting)
*   **Architecture Pattern:** Feature-based component organization (`/components/agents/`, `/components/memory/`, etc.)

## 2. Next.js App Router Standards

### Project Structure Requirements
*   **MANDATORY:** Use Next.js 14+ App Router exclusively (NEVER Pages Router)
*   **REQUIRED:** Implement proper file-based routing structure:
    ```
    app/
    ├── layout.tsx         # Root layout component
    ├── page.tsx          # Home page
    ├── (auth)/           # Route groups
    │   ├── layout.tsx
    │   ├── login/
    │   └── register/
    ├── (dashboard)/      # Protected routes
    │   ├── agents/
    │   ├── memory/
    │   └── settings/
    components/
    ├── ui/               # Base UI components
    ├── agents/           # Agent-specific components
    ├── memory/           # Memory management UI
    └── layout/           # Layout components
    ```

### Component Architecture
*   **CRITICAL:** Use Server Components by default, Client Components only when necessary
*   **MANDATORY:** Mark Client Components explicitly with `'use client'` directive
*   **REQUIRED:** Implement proper error boundaries and loading states
*   **REQUIRED:** Use Suspense for data fetching and code splitting

```tsx
// Server Component (default)
export default async function AgentsPage() {
  const agents = await fetchAgents();
  return <AgentList agents={agents} />;
}

// Client Component (when needed)
'use client'
export default function InteractiveAgent() {
  const [state, setState] = useState();
  return <div>Interactive content</div>;
}
```

## 3. TypeScript Strict Standards

### Configuration Requirements
*   **CRITICAL:** Use TypeScript 5.x with strict configuration
*   **MANDATORY:** Enable all strict mode flags:
    - `"strict": true`
    - `"noUncheckedIndexedAccess": true`
    - `"exactOptionalPropertyTypes": true`
    - `"noImplicitOverride": true`
    - `"useDefineForClassFields": true`
    - `"verbatimModuleSyntax": true`

### Type Safety Standards
*   **CRITICAL:** NEVER use `any` type unless explicitly justified with comments
*   **MANDATORY:** NEVER use `@ts-ignore` or `@ts-expect-error` to suppress TypeScript errors
*   **REQUIRED:** Use proper type annotations for all function parameters and return types
*   **CRITICAL:** Implement proper error boundaries with TypeScript

```tsx
// Proper typing example
interface AgentProps {
  id: string;
  name: string;
  description?: string;
  onUpdate: (id: string, data: AgentUpdateData) => Promise<void>;
}

export function Agent({ id, name, description, onUpdate }: AgentProps) {
  // Implementation with full type safety
}
```

### Result Types for Error Handling
*   **REQUIRED:** Use `Result<T, E>` types for fallible operations
*   **MANDATORY:** Implement proper error boundaries in React
*   **CRITICAL:** Handle loading and error states appropriately

```tsx
type Result<T, E = Error> = 
  | { success: true; data: T }
  | { success: false; error: E };

async function fetchAgent(id: string): Promise<Result<Agent>> {
  try {
    const agent = await api.getAgent(id);
    return { success: true, data: agent };
  } catch (error) {
    return { success: false, error: error as Error };
  }
}
```

## 4. React 18 Standards

### Component Patterns
*   **REQUIRED:** Use functional components with hooks (no class components)
*   **MANDATORY:** Use React 18 concurrent features (Suspense, transitions)
*   **CRITICAL:** Implement proper cleanup in useEffect hooks
*   **REQUIRED:** Use proper dependency arrays in hooks

```tsx
import { useState, useEffect, useTransition } from 'react';

export function AgentManager() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    const controller = new AbortController();
    
    fetchAgents({ signal: controller.signal })
      .then(setAgents)
      .catch(console.error);
    
    return () => controller.abort();
  }, []);

  const updateAgent = (id: string, data: AgentUpdateData) => {
    startTransition(() => {
      // Non-blocking update
    });
  };

  return <div>Agent management UI</div>;
}
```

### Performance Optimization
*   **REQUIRED:** Use React.memo for expensive components
*   **MANDATORY:** Implement proper key props for list items
*   **CRITICAL:** Use dynamic imports for code splitting
*   **REQUIRED:** Optimize bundle size with proper tree shaking

## 5. Biome Linting and Formatting Standards

### Configuration
*   **CRITICAL:** Biome is the SINGLE source of truth for linting and formatting
*   **MANDATORY:** Use 2-space indentation, single quotes, trailing commas
*   **REQUIRED:** Configure proper file patterns and exclusions

```json
{
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "correctness": {
        "noUnusedVariables": "error"
      },
      "suspicious": {
        "noExplicitAny": "error"
      }
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "quoteStyle": "single"
  }
}
```

### Code Suppression
*   **REQUIRED:** Provide explanations for ALL suppressions
*   **CRITICAL:** Use specific suppression comments, not blanket ignores

```tsx
// biome-ignore lint/suspicious/noExplicitAny: Legacy API requires any type
const legacyData: any = getLegacyData();
```

## 6. Styling and UI Standards
*   **REQUIRED:** Use Tailwind CSS for styling
*   **MANDATORY:** Implement responsive design with mobile-first approach
*   **CRITICAL:** Follow accessibility guidelines (WCAG 2.1 AA compliance)
*   **REQUIRED:** Use semantic HTML elements appropriately

## 7. State Management
*   **REQUIRED:** Use React hooks for local state management
*   **MANDATORY:** Implement proper state updates with immutable patterns
*   **CRITICAL:** Use context sparingly, prefer prop drilling for simple cases
*   **REQUIRED:** Implement proper loading and error states

## 8. API Integration
*   **REQUIRED:** Use proper TypeScript types for API responses
*   **MANDATORY:** Implement proper error handling for API calls
*   **CRITICAL:** Use proper caching strategies for data fetching
*   **REQUIRED:** Implement proper loading states during API calls

```tsx
async function useAgents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAgents()
      .then(setAgents)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { agents, loading, error };
}
```

## 9. Testing Standards
*   **MANDATORY:** Use Jest with React Testing Library for component tests
*   **REQUIRED:** Mock all external dependencies using MSW (Mock Service Worker)
*   **CRITICAL:** Test user interactions, not implementation details
*   **REQUIRED:** Maintain high test coverage for critical components

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Agent } from './Agent';

test('should handle agent update', async () => {
  const mockUpdate = jest.fn();
  render(<Agent id="1" name="Test" onUpdate={mockUpdate} />);
  
  fireEvent.click(screen.getByText('Update'));
  expect(mockUpdate).toHaveBeenCalledWith('1', expect.any(Object));
});
```

## 10. Performance and Bundle Optimization
*   **REQUIRED:** Use `next/image` for all images
*   **MANDATORY:** Use `next/font` for font optimization
*   **CRITICAL:** Implement proper code splitting with dynamic imports
*   **REQUIRED:** Monitor bundle size and performance metrics

## 11. Security Standards
*   **CRITICAL:** NEVER use `dangerouslySetInnerHTML` without proper sanitization
*   **MANDATORY:** Validate all user inputs on both client and server sides
*   **REQUIRED:** Implement proper CSP headers and security best practices
*   **CRITICAL:** Never expose sensitive information in client-side code

## 12. Forbidden Patterns
*   **NEVER** use `any` type without explicit justification
*   **NEVER** suppress TypeScript errors with ignore comments
*   **NEVER** use class components (use functional components only)
*   **NEVER** directly mutate state objects (use immutable updates)
*   **NEVER** ignore accessibility requirements
*   **NEVER** hardcode API URLs or sensitive configuration
*   **NEVER** use Pages Router (App Router only)

## 13. Programmatic Checks
*   **MANDATORY:** Run `npm run lint` before committing changes
*   **MANDATORY:** Run `npm run type-check` to verify TypeScript types

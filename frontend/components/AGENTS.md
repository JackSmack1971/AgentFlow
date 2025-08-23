# AGENTS.md: Component Development Guidelines

This document provides specific guidance for AI models working with React components in `/frontend/components/`. These guidelines are derived from the React 18, TypeScript 5.x, Next.js, and Biome rulesets.

## 1. Project Scope & Architecture
*   **Primary Purpose:** Reusable React 18 components with TypeScript for the AgentFlow frontend
*   **Core Technologies:** React 18+, TypeScript 5.x, Next.js 14+ App Router, Tailwind CSS
*   **Architecture Pattern:** Feature-based component organization with clear separation between UI and business logic

## 2. Component Organization Standards

### Directory Structure Requirements
*   **MANDATORY:** Organize components by feature and complexity:
    ```
    components/
    ├── ui/                      # Base UI components (design system)
    │   ├── button.tsx
    │   ├── input.tsx
    │   ├── modal.tsx
    │   ├── toast.tsx
    │   └── index.ts            # Export barrel
    ├── agents/                  # Agent-specific components
    │   ├── agent-card.tsx
    │   ├── agent-form.tsx
    │   ├── agent-list.tsx
    │   └── agent-wizard/       # Complex components in folders
    │       ├── index.tsx
    │       ├── step-config.tsx
    │       └── step-tools.tsx
    ├── memory/                  # Memory management UI
    │   ├── memory-browser.tsx
    │   ├── memory-search.tsx
    │   └── memory-inspector.tsx
    ├── layout/                  # Layout components
    │   ├── header.tsx
    │   ├── sidebar.tsx
    │   ├── navigation.tsx
    │   └── error-boundary.tsx
    └── common/                  # Shared utility components
        ├── loading-spinner.tsx
        ├── error-message.tsx
        └── confirmation-dialog.tsx
    ```

### Component Naming Conventions [TypeScript Ruleset]
*   **REQUIRED:** Use PascalCase for component names
*   **MANDATORY:** Use kebab-case for file names
*   **CRITICAL:** Use descriptive, domain-specific component names
*   **REQUIRED:** Export components as default exports with named types

## 3. TypeScript Component Standards [Hard Constraint]

### Component Type Definitions
*   **CRITICAL:** Define comprehensive TypeScript interfaces for all props
*   **MANDATORY:** Use strict typing with no `any` types
*   **REQUIRED:** Export prop types for reusability
*   **CRITICAL:** Use proper generic constraints for flexible components

```tsx
import { ReactNode, HTMLAttributes, forwardRef } from 'react';

// Strict prop type definitions
interface AgentCardProps {
  id: string;
  name: string;
  description?: string;
  status: 'active' | 'inactive' | 'training' | 'error';
  modelProvider: 'openai' | 'anthropic' | 'google' | 'local';
  runCount: number;
  createdAt: Date;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onRun: (id: string) => Promise<void>;
  className?: string;
  'data-testid'?: string;
}

// Component with proper TypeScript
export default function AgentCard({
  id,
  name,
  description,
  status,
  modelProvider,
  runCount,
  createdAt,
  onEdit,
  onDelete,
  onRun,
  className = '',
  'data-testid': testId
}: AgentCardProps) {
  // Implementation with full type safety
}

// Export types for reuse
export type { AgentCardProps };
```

### Generic Component Patterns
*   **REQUIRED:** Use generic types for flexible, reusable components
*   **MANDATORY:** Provide proper constraint types for generics
*   **CRITICAL:** Maintain type safety in generic implementations
*   **REQUIRED:** Document generic type parameters

```tsx
// Generic list component with type safety
interface ListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => ReactNode;
  keyExtractor: (item: T) => string;
  loading?: boolean;
  emptyMessage?: string;
  className?: string;
}

export default function List<T>({
  items,
  renderItem,
  keyExtractor,
  loading = false,
  emptyMessage = 'No items found',
  className = ''
}: ListProps<T>) {
  if (loading) {
    return <div className="animate-pulse">Loading...</div>;
  }

  if (items.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className={className}>
      {items.map((item, index) => (
        <div key={keyExtractor(item)}>
          {renderItem(item, index)}
        </div>
      ))}
    </div>
  );
}

// Usage with type safety
/*
<List<Agent>
  items={agents}
  renderItem={(agent) => <AgentCard {...agent} />}
  keyExtractor={(agent) => agent.id}
/>
*/
```

## 4. React 18 Component Patterns [Hard Constraint]

### Functional Components Only
*   **MANDATORY:** Use only functional components with hooks (no class components)
*   **REQUIRED:** Use React 18 concurrent features (Suspense, transitions)
*   **CRITICAL:** Implement proper cleanup in useEffect hooks
*   **REQUIRED:** Use proper dependency arrays in all hooks

```tsx
import { useState, useEffect, useTransition, startTransition } from 'react';
import { Agent } from '@/types/agent';

interface AgentListProps {
  initialAgents?: Agent[];
  onAgentSelect?: (agent: Agent) => void;
}

export default function AgentList({ initialAgents = [], onAgentSelect }: AgentListProps) {
  const [agents, setAgents] = useState<Agent[]>(initialAgents);
  const [loading, setLoading] = useState(false);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    const controller = new AbortController();
    
    async function fetchAgents() {
      try {
        setLoading(true);
        const response = await fetch('/api/agents', {
          signal: controller.signal
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch agents');
        }
        
        const fetchedAgents = await response.json();
        setAgents(fetchedAgents);
      } catch (error) {
        if (!controller.signal.aborted) {
          console.error('Failed to fetch agents:', error);
        }
      } finally {
        setLoading(false);
      }
    }

    if (initialAgents.length === 0) {
      fetchAgents();
    }

    // Cleanup function
    return () => {
      controller.abort();
    };
  }, [initialAgents.length]);

  const handleAgentClick = (agent: Agent) => {
    startTransition(() => {
      onAgentSelect?.(agent);
    });
  };

  return (
    <div className="space-y-4">
      {loading && <div>Loading agents...</div>}
      {isPending && <div>Updating...</div>}
      {agents.map((agent) => (
        <AgentCard
          key={agent.id}
          {...agent}
          onClick={() => handleAgentClick(agent)}
        />
      ))}
    </div>
  );
}
```

### Error Boundaries
*   **REQUIRED:** Implement error boundaries for component trees
*   **MANDATORY:** Use class components only for error boundaries
*   **CRITICAL:** Provide meaningful error messages and recovery options
*   **REQUIRED:** Log errors for debugging purposes

```tsx
'use client'; // Required for error boundaries in App Router

import { Component, ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('Component error caught by boundary:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
            <h3 className="text-lg font-semibold text-red-800">
              Something went wrong
            </h3>
            <p className="text-red-600 mt-2">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: undefined })}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Try Again
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
```

## 5. Component Composition Patterns

### Compound Components
*   **REQUIRED:** Use compound component pattern for complex UI components
*   **MANDATORY:** Maintain type safety in compound implementations
*   **CRITICAL:** Provide clear API boundaries for compound parts
*   **REQUIRED:** Document compound component usage patterns

```tsx
import { createContext, useContext, ReactNode } from 'react';

// Modal compound component pattern
interface ModalContextValue {
  isOpen: boolean;
  onClose: () => void;
}

const ModalContext = createContext<ModalContextValue | null>(null);

function useModalContext() {
  const context = useContext(ModalContext);
  if (!context) {
    throw new Error('Modal components must be used within Modal.Root');
  }
  return context;
}

interface ModalRootProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
}

function ModalRoot({ isOpen, onClose, children }: ModalRootProps) {
  return (
    <ModalContext.Provider value={{ isOpen, onClose }}>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div 
            className="fixed inset-0 bg-black bg-opacity-50"
            onClick={onClose}
          />
          <div className="relative bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
            {children}
          </div>
        </div>
      )}
    </ModalContext.Provider>
  );
}

function ModalHeader({ children }: { children: ReactNode }) {
  const { onClose } = useModalContext();
  
  return (
    <div className="flex justify-between items-center p-6 border-b">
      <div>{children}</div>
      <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
        ×
      </button>
    </div>
  );
}

function ModalBody({ children }: { children: ReactNode }) {
  return <div className="p-6">{children}</div>;
}

function ModalFooter({ children }: { children: ReactNode }) {
  return <div className="p-6 border-t bg-gray-50">{children}</div>;
}

// Export as compound component
const Modal = {
  Root: ModalRoot,
  Header: ModalHeader,
  Body: ModalBody,
  Footer: ModalFooter
};

export default Modal;

// Usage:
/*
<Modal.Root isOpen={isOpen} onClose={() => setIsOpen(false)}>
  <Modal.Header>
    <h2>Agent Configuration</h2>
  </Modal.Header>
  <Modal.Body>
    <AgentForm />
  </Modal.Body>
  <Modal.Footer>
    <button>Save</button>
    <button>Cancel</button>
  </Modal.Footer>
</Modal.Root>
*/
```

## 6. Form Component Patterns

### React Hook Form Integration
*   **REQUIRED:** Use React Hook Form for all form components
*   **MANDATORY:** Implement proper form validation with Zod
*   **CRITICAL:** Provide type-safe form handling
*   **REQUIRED:** Handle form errors gracefully

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Zod schema for form validation
const agentFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name too long'),
  description: z.string().max(500, 'Description too long').optional(),
  model: z.string().min(1, 'Model is required'),
  temperature: z.number().min(0).max(2),
  maxTokens: z.number().min(1).max(32000),
  systemPrompt: z.string().max(2000, 'System prompt too long').optional(),
});

type AgentFormData = z.infer<typeof agentFormSchema>;

interface AgentFormProps {
  initialData?: Partial<AgentFormData>;
  onSubmit: (data: AgentFormData) => Promise<void>;
  onCancel?: () => void;
  isLoading?: boolean;
}

export default function AgentForm({ 
  initialData, 
  onSubmit, 
  onCancel, 
  isLoading = false 
}: AgentFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset
  } = useForm<AgentFormData>({
    resolver: zodResolver(agentFormSchema),
    defaultValues: {
      name: '',
      description: '',
      model: 'gpt-4',
      temperature: 0.7,
      maxTokens: 1000,
      systemPrompt: '',
      ...initialData
    }
  });

  const onFormSubmit = async (data: AgentFormData) => {
    try {
      await onSubmit(data);
      reset();
    } catch (error) {
      console.error('Form submission failed:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Agent Name *
        </label>
        <input
          {...register('name')}
          type="text"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          disabled={isLoading || isSubmitting}
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">
          Description
        </label>
        <textarea
          {...register('description')}
          rows={3}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          disabled={isLoading || isSubmitting}
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
        )}
      </div>

      <div className="flex space-x-4">
        <button
          type="submit"
          disabled={isLoading || isSubmitting}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Saving...' : 'Save Agent'}
        </button>
        
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading || isSubmitting}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
```

## 7. Performance Optimization

### React.memo and Optimization
*   **REQUIRED:** Use React.memo for expensive components
*   **MANDATORY:** Implement proper memoization strategies
*   **CRITICAL:** Use callback memoization to prevent unnecessary re-renders
*   **REQUIRED:** Monitor component performance with React DevTools

```tsx
import { memo, useCallback, useMemo } from 'react';

interface ExpensiveListItemProps {
  item: {
    id: string;
    name: string;
    data: unknown;
  };
  onUpdate: (id: string, data: unknown) => void;
  onDelete: (id: string) => void;
}

// Memoized component to prevent unnecessary re-renders
const ExpensiveListItem = memo(function ExpensiveListItem({
  item,
  onUpdate,
  onDelete
}: ExpensiveListItemProps) {
  // Expensive computation that should be memoized
  const processedData = useMemo(() => {
    return processComplexData(item.data);
  }, [item.data]);

  // Memoized callbacks to prevent child re-renders
  const handleUpdate = useCallback(() => {
    onUpdate(item.id, processedData);
  }, [item.id, processedData, onUpdate]);

  const handleDelete = useCallback(() => {
    onDelete(item.id);
  }, [item.id, onDelete]);

  return (
    <div className="border rounded p-4">
      <h3>{item.name}</h3>
      <div>{processedData}</div>
      <div className="mt-2 space-x-2">
        <button onClick={handleUpdate}>Update</button>
        <button onClick={handleDelete}>Delete</button>
      </div>
    </div>
  );
});

// Custom comparison function for complex props
const ExpensiveListItemWithComparison = memo(function ExpensiveListItem(props: ExpensiveListItemProps) {
  // Component implementation
}, (prevProps, nextProps) => {
  return (
    prevProps.item.id === nextProps.item.id &&
    prevProps.item.name === nextProps.item.name &&
    JSON.stringify(prevProps.item.data) === JSON.stringify(nextProps.item.data)
  );
});

export default ExpensiveListItem;

function processComplexData(data: unknown): string {
  // Expensive processing logic
  return JSON.stringify(data);
}
```

## 8. Accessibility Standards [Hard Constraint]

### WCAG 2.1 AA Compliance
*   **CRITICAL:** Include proper ARIA labels and roles
*   **MANDATORY:** Ensure keyboard navigation support
*   **REQUIRED:** Implement proper focus management
*   **CRITICAL:** Use semantic HTML elements appropriately

```tsx
import { useRef, useEffect, KeyboardEvent } from 'react';

interface AccessibleButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
  loading?: boolean;
  ariaLabel?: string;
  ariaDescribedBy?: string;
}

export default function AccessibleButton({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  loading = false,
  ariaLabel,
  ariaDescribedBy
}: AccessibleButtonProps) {
  const buttonRef = useRef<HTMLButtonElement>(null);

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === ' ' || event.key === 'Enter') {
      event.preventDefault();
      if (!disabled && !loading) {
        onClick();
      }
    }
  };

  const baseClasses = 'px-4 py-2 rounded font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors';
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
  };
  
  const disabledClasses = 'opacity-50 cursor-not-allowed';

  return (
    <button
      ref={buttonRef}
      className={`${baseClasses} ${variantClasses[variant]} ${disabled || loading ? disabledClasses : ''}`}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      disabled={disabled || loading}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      aria-disabled={disabled || loading}
      type="button"
    >
      {loading ? (
        <>
          <span className="sr-only">Loading</span>
          <div className="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full mr-2" />
          Loading...
        </>
      ) : (
        children
      )}
    </button>
  );
}
```

## 9. Testing Components

### Component Testing Standards
*   **REQUIRED:** Test user interactions, not implementation details
*   **MANDATORY:** Use React Testing Library with proper assertions
*   **CRITICAL:** Mock external dependencies appropriately
*   **REQUIRED:** Test accessibility features

```tsx
// Example test file structure (for reference)
/*
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AgentForm from './agent-form';

describe('AgentForm', () => {
  const mockSubmit = jest.fn();
  
  beforeEach(() => {
    mockSubmit.mockClear();
  });

  it('should render form fields correctly', () => {
    render(<AgentForm onSubmit={mockSubmit} />);
    
    expect(screen.getByLabelText(/agent name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /save agent/i })).toBeInTheDocument();
  });

  it('should validate required fields', async () => {
    const user = userEvent.setup();
    render(<AgentForm onSubmit={mockSubmit} />);
    
    await user.click(screen.getByRole('button', { name: /save agent/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/name is required/i)).toBeInTheDocument();
    });
    
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('should submit valid form data', async () => {
    const user = userEvent.setup();
    render(<AgentForm onSubmit={mockSubmit} />);
    
    await user.type(screen.getByLabelText(/agent name/i), 'Test Agent');
    await user.click(screen.getByRole('button', { name: /save agent/i }));
    
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        name: 'Test Agent',
        model: 'gpt-4',
        temperature: 0.7,
        // ... other default values
      });
    });
  });
});
*/
```

## 10. Forbidden Patterns
*   **NEVER** use class components except for error boundaries
*   **NEVER** directly mutate props or state objects
*   **NEVER** use `any` type without explicit justification
*   **NEVER** skip error boundaries for complex component trees
*   **NEVER** ignore accessibility requirements (ARIA labels, keyboard support)
*   **NEVER** use inline functions as props without memoization for expensive components
*   **NEVER** skip proper cleanup in useEffect hooks
*   **NEVER** ignore TypeScript errors with `@ts-ignore` or similar

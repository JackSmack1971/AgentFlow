# Project Overview & Purpose

This file provides essential guidance for AI agents working with the UI components located in `/frontend/components/ui/` and complex interactive components throughout the frontend. These components power the AgentFlow platform - a unified AI agent development platform that integrates six leading frameworks to reduce agent development time by 60-80%. The UI architecture supports a three-column layout with sophisticated interactive components including visual workflow editors, real-time streaming interfaces, and enterprise-grade management dashboards.

## Architecture & Key Files

**Primary Technologies:** Next.js 14+ App Router, React 18+, TypeScript 5.x, Tailwind CSS, Biome linting
**Architecture Pattern:** Three-column layout with progressive disclosure, supporting both foundational UI primitives and complex interactive components

### Critical Component Structure
```
frontend/components/ui/
├── foundational/           # Base design system components
│   ├── button.tsx             # Action components with loading states
│   ├── input.tsx              # Form inputs with validation states
│   ├── modal.tsx              # Modal system with focus management
│   ├── toast.tsx              # Notification system with auto-dismiss
│   ├── dropdown.tsx           # Dropdown menus with keyboard navigation
│   ├── card.tsx               # Content containers for dashboard grids
│   ├── badge.tsx              # Status indicators for agents/services
│   ├── progress.tsx           # Progress bars for ingestion/processing
│   ├── skeleton.tsx           # Loading placeholders for async content
│   └── data-table.tsx         # Sortable/filterable tables for runs history
├── interactive/            # Complex interactive components
│   ├── node-canvas.tsx        # Visual workflow editor for LangGraph
│   ├── streaming-terminal.tsx # Real-time agent response display
│   ├── knowledge-graph.tsx    # Interactive graph visualization
│   ├── trace-viewer.tsx       # Hierarchical execution trace display
│   ├── memory-browser.tsx     # Multi-scope memory management interface
│   ├── semantic-search.tsx    # Hybrid search with relevance scoring
│   └── metrics-dashboard.tsx  # Performance visualization components
├── layout/                 # Three-column layout components
│   ├── app-layout.tsx         # Main three-column structure
│   ├── navigation-sidebar.tsx # Persistent left navigation
│   ├── content-area.tsx       # Adaptive main content region
│   ├── context-panel.tsx      # Optional right panel for real-time data
│   └── global-header.tsx      # User profile, org selector, search
└── index.ts                # Export barrel for clean imports
```

**Real-time Integration Points:**
- **WebSocket connections** for health status and live updates
- **EventSource streams** for agent execution and ingestion progress
- **React Query/SWR** for optimistic updates and cache management

## Development Environment & Commands

**Prerequisites:** Node.js 20+, npm, TypeScript 5.x compiler, WebSocket support

### Component Development Workflow
```bash
# Start frontend development server with API proxy (from /frontend/)
npm run dev

# Start with WebSocket support for real-time features
npm run dev:ws

# Run TypeScript type checking with strict mode
npm run type-check

# Run Biome linting and formatting
npm run lint
npm run format

# Run component tests with coverage including interaction testing
npm run test
npm run test:coverage

# Run accessibility testing with axe-core
npm run test:a11y

# Run visual regression tests for complex components
npm run test:visual

# Build for production with optimization
npm run build
```

### Real-time Feature Testing Commands
```bash
# Test WebSocket connections
npm run test:websockets

# Test EventSource streaming
npm run test:streaming

# Test canvas interactions (node editor)
npm run test:canvas

# Test knowledge graph rendering performance
npm run test:graph-performance
```

**CRITICAL:** All interactive components MUST handle connection failures gracefully with automatic reconnection and user feedback.

## Code Style & Conventions

### Complex Component Architecture Standards
**MANDATORY Interactive Component Structure:**
```tsx
import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useWebSocket } from '../../hooks/use-websocket';
import { useCanvasInteractions } from '../../hooks/use-canvas-interactions';
import { cn } from '../../lib/utils';

interface NodeCanvasProps {
  agentId: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeUpdate: (nodeId: string, data: NodeData) => void;
  onConnectionCreate: (source: string, target: string) => void;
  readonly?: boolean;
  className?: string;
}

export const NodeCanvas: React.FC<NodeCanvasProps> = ({
  agentId,
  nodes,
  edges,
  onNodeUpdate,
  onConnectionCreate,
  readonly = false,
  className
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedNodes, setSelectedNodes] = useState<Set<string>>(new Set());
  const [dragState, setDragState] = useState<DragState | null>(null);
  
  // WebSocket for real-time collaboration
  const { send: sendUpdate, lastMessage } = useWebSocket(
    `ws://localhost:8000/agents/${agentId}/canvas`,
    {
      onOpen: () => console.log('Canvas WebSocket connected'),
      onError: (error) => console.error('Canvas WebSocket error:', error),
      shouldReconnect: () => true,
    }
  );

  // Canvas interaction handling
  const {
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleKeyDown,
  } = useCanvasInteractions({
    nodes,
    edges,
    selectedNodes,
    onNodeUpdate,
    onConnectionCreate,
    canvasRef,
    readonly,
  });

  // Keyboard accessibility for canvas
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target !== canvasRef.current) return;
      
      switch (e.key) {
        case 'Delete':
          selectedNodes.forEach(nodeId => onNodeUpdate(nodeId, { deleted: true }));
          break;
        case 'Escape':
          setSelectedNodes(new Set());
          break;
        case 'ArrowLeft':
        case 'ArrowRight':
        case 'ArrowUp':
        case 'ArrowDown':
          e.preventDefault();
          handleKeyDown(e);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [selectedNodes, handleKeyDown, onNodeUpdate]);

  return (
    <div className={cn(
      'relative flex-1 overflow-hidden border border-gray-200 rounded-lg',
      'focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500',
      className
    )}>
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-crosshair focus:outline-none"
        tabIndex={0}
        role="img"
        aria-label="Agent workflow canvas"
        aria-describedby="canvas-instructions"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      />
      <div 
        id="canvas-instructions" 
        className="sr-only"
      >
        Use arrow keys to move nodes, Delete to remove selected nodes, 
        Escape to clear selection. Click and drag to select multiple nodes.
      </div>
      
      {/* Node properties panel overlay */}
      {selectedNodes.size === 1 && (
        <NodePropertiesPanel 
          nodeId={Array.from(selectedNodes)[0]}
          onUpdate={onNodeUpdate}
          className="absolute top-4 right-4 w-80"
        />
      )}
    </div>
  );
};
```

### Real-time Component Standards
- **CRITICAL:** All streaming components MUST handle connection interruptions with automatic reconnection
- **MANDATORY:** Use React.memo() for expensive renders with proper dependency arrays
- **REQUIRED:** Implement proper cleanup for WebSocket/EventSource connections
- **CRITICAL:** Debounce user interactions to prevent overwhelming the backend
- **REQUIRED:** Use Web Workers for heavy computations (graph algorithms, large data processing)

### Canvas & Interactive Component Requirements
- **MANDATORY:** Support keyboard navigation for accessibility
- **CRITICAL:** Implement proper ARIA labels for complex visualizations
- **REQUIRED:** Use requestAnimationFrame for smooth animations
- **CRITICAL:** Implement virtualization for large data sets (>1000 nodes/items)
- **REQUIRED:** Provide alternative text descriptions for visual components

### Performance Standards for Complex Components
```tsx
// Virtualization for large lists
import { FixedSizeList as List } from 'react-window';

// Memoization for expensive components
const MemoizedTraceNode = React.memo(TraceNode, (prevProps, nextProps) => {
  return prevProps.trace.id === nextProps.trace.id && 
         prevProps.expanded === nextProps.expanded;
});

// Web Worker for graph algorithms
const useGraphLayout = (nodes: GraphNode[], edges: GraphEdge[]) => {
  const [layout, setLayout] = useState<NodePosition[]>([]);
  
  useEffect(() => {
    const worker = new Worker('/workers/graph-layout.worker.js');
    worker.postMessage({ nodes, edges });
    worker.onmessage = (e) => setLayout(e.data.positions);
    return () => worker.terminate();
  }, [nodes, edges]);
  
  return layout;
};
```

## Testing & Validation Protocol

### Complex Component Testing Framework
**Testing Stack:** Jest + React Testing Library + Canvas Testing Utilities + WebSocket Mocks
**Coverage Requirement:** ≥95% for foundational components, ≥85% for complex interactive components

### Required Test Categories for Interactive Components
```tsx
// Example: node-canvas.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NodeCanvas } from './node-canvas';
import { MockWebSocketServer } from '../../test-utils/mock-websocket';

describe('NodeCanvas', () => {
  let mockWsServer: MockWebSocketServer;

  beforeEach(() => {
    mockWsServer = new MockWebSocketServer('ws://localhost:8000/agents/test/canvas');
  });

  afterEach(() => {
    mockWsServer.close();
  });

  // 1. Canvas Rendering Tests
  it('renders canvas with proper ARIA labels', () => {
    render(<NodeCanvas agentId="test" nodes={[]} edges={[]} />);
    
    const canvas = screen.getByRole('img', { name: /agent workflow canvas/i });
    expect(canvas).toBeInTheDocument();
    expect(canvas).toHaveAttribute('tabIndex', '0');
  });

  // 2. Keyboard Navigation Tests
  it('supports keyboard node movement', async () => {
    const mockOnNodeUpdate = jest.fn();
    const nodes = [{ id: 'node1', x: 100, y: 100, type: 'start' }];
    
    render(
      <NodeCanvas 
        agentId="test" 
        nodes={nodes} 
        edges={[]} 
        onNodeUpdate={mockOnNodeUpdate}
      />
    );
    
    const canvas = screen.getByRole('img');
    canvas.focus();
    
    // Select node first (mock click)
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseUp(canvas);
    
    // Move with keyboard
    fireEvent.keyDown(canvas, { key: 'ArrowRight' });
    
    await waitFor(() => {
      expect(mockOnNodeUpdate).toHaveBeenCalledWith(
        'node1',
        expect.objectContaining({ x: 105 })
      );
    });
  });

  // 3. WebSocket Integration Tests
  it('handles real-time collaboration updates', async () => {
    const mockOnNodeUpdate = jest.fn();
    
    render(<NodeCanvas agentId="test" nodes={[]} edges={[]} onNodeUpdate={mockOnNodeUpdate} />);
    
    // Simulate receiving update from another user
    mockWsServer.send({
      type: 'node_update',
      nodeId: 'node1',
      data: { x: 200, y: 150 }
    });
    
    await waitFor(() => {
      expect(mockOnNodeUpdate).toHaveBeenCalledWith('node1', { x: 200, y: 150 });
    });
  });

  // 4. Performance Tests
  it('handles large graphs without performance degradation', async () => {
    const startTime = performance.now();
    const largeNodes = Array.from({ length: 1000 }, (_, i) => ({
      id: `node${i}`,
      x: Math.random() * 1000,
      y: Math.random() * 1000,
      type: 'process'
    }));
    
    render(<NodeCanvas agentId="test" nodes={largeNodes} edges={[]} />);
    
    const renderTime = performance.now() - startTime;
    expect(renderTime).toBeLessThan(100); // Should render in under 100ms
  });

  // 5. Error Handling Tests
  it('gracefully handles WebSocket disconnection', async () => {
    const { container } = render(<NodeCanvas agentId="test" nodes={[]} edges={[]} />);
    
    // Simulate connection loss
    mockWsServer.close();
    
    // Should show reconnection indicator
    await waitFor(() => {
      expect(container.querySelector('[data-testid="reconnecting-indicator"]')).toBeInTheDocument();
    });
  });
});

// Streaming Terminal Tests
describe('StreamingTerminal', () => {
  it('handles EventSource streams with proper cleanup', async () => {
    const mockEventSource = jest.fn().mockImplementation(() => ({
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      close: jest.fn(),
    }));
    
    global.EventSource = mockEventSource;
    
    const { unmount } = render(
      <StreamingTerminal agentId="test" runId="run123" />
    );
    
    expect(mockEventSource).toHaveBeenCalledWith('/api/runs/run123/stream');
    
    unmount();
    
    // Should cleanup EventSource
    expect(mockEventSource().close).toHaveBeenCalled();
  });
});
```

### Validation Commands (MUST Execute After Changes)
```bash
# Type checking with complex component validation
npm run type-check

# Comprehensive linting including canvas components
npm run lint

# Full test suite including interaction tests
npm run test -- --coverage --testPathPattern="ui|interactive"

# Canvas-specific accessibility testing
npm run test:canvas-a11y

# WebSocket/streaming integration tests
npm run test:real-time

# Performance tests for complex components
npm run test:performance

# Visual regression tests
npm run test:visual -- --updateSnapshot
```

**CRITICAL VALIDATION RULE:** Agents MUST execute ALL validation commands and ensure they pass before completing any UI component task. Special attention required for WebSocket cleanup, canvas accessibility, and performance thresholds.

## Pull Request (PR) Instructions

### PR Title Format (MANDATORY)
```
[UI] <Component Type>: <Short description>

Examples:
[UI] Interactive: Add node canvas with real-time collaboration
[UI] Streaming: Implement agent execution terminal with EventSource
[UI] Dashboard: Add memory browser with semantic search
[UI] Foundation: Update button component with loading states
```

### Required PR Body Sections
```markdown
## Description:
Brief description of UI component changes and interaction/performance impact.

## Component Updates:
- [ ] Component functionality implemented with proper TypeScript interfaces
- [ ] Real-time features tested with WebSocket/EventSource mocking
- [ ] Canvas/interactive components support keyboard navigation
- [ ] Performance optimizations implemented (virtualization, memoization)
- [ ] Error boundaries and connection failure handling added

## Testing Done:
- [ ] Unit tests with ≥85% coverage for complex components (≥95% for foundational)
- [ ] Interaction tests for keyboard navigation and accessibility
- [ ] WebSocket/EventSource connection and cleanup testing
- [ ] Performance testing with large data sets (>1000 items)
- [ ] Visual regression tests for complex visualizations
- [ ] Cross-browser testing for canvas and streaming features

## Accessibility Checklist:
- [ ] Keyboard navigation functional for all interactive elements
- [ ] ARIA labels and descriptions for complex visualizations
- [ ] Screen reader compatibility with dynamic content announcements
- [ ] High contrast support and focus indicators
- [ ] Alternative text descriptions for visual-only information

## Performance Checklist:
- [ ] Components handle >1000 data items without lag
- [ ] Canvas rendering uses requestAnimationFrame
- [ ] WebSocket reconnection logic doesn't create memory leaks
- [ ] Large components use virtualization or pagination
- [ ] Expensive computations moved to Web Workers

## Screenshots/Videos:
[Include recordings of complex interactions, canvas operations, streaming responses]
```

## Security & Non-Goals

### Security Guidelines for Interactive Components
- **CRITICAL:** Sanitize all data received via WebSocket/EventSource connections
- **MANDATORY:** Validate graph data structures to prevent infinite loops or crashes
- **REQUIRED:** Implement proper authentication for real-time connections
- **CRITICAL:** Rate-limit user interactions to prevent backend overload
- **REQUIRED:** Sanitize canvas rendering data to prevent XSS via SVG/HTML injection

### Real-time Connection Security
```tsx
// Secure WebSocket connection with authentication
const useSecureWebSocket = (url: string, token: string) => {
  return useWebSocket(`${url}?token=${encodeURIComponent(token)}`, {
    onOpen: () => console.log('Authenticated WebSocket connected'),
    onError: (error) => console.error('WebSocket authentication failed:', error),
    shouldReconnect: (closeEvent) => closeEvent.code !== 4001, // Don't reconnect on auth failure
  });
};
```

### Non-Goals (DO NOT Implement)
- **FORBIDDEN:** Direct canvas manipulation without proper event handling
- **FORBIDDEN:** WebSocket connections without proper cleanup and error handling  
- **FORBIDDEN:** Complex visualizations without keyboard accessibility
- **FORBIDDEN:** Real-time features without offline graceful degradation
- **FORBIDDEN:** Canvas components without ARIA labels and descriptions
- **FORBIDDEN:** Streaming components without connection failure recovery
- **FORBIDDEN:** Performance-heavy operations on the main thread
- **FORBIDDEN:** Complex state management without proper TypeScript typing
- **FORBIDDEN:** Interactive components without comprehensive interaction testing

**Component Scope:** This directory contains both foundational UI primitives and sophisticated interactive components. Complex business logic belongs in custom hooks or services, never embedded directly in UI components. All components must support the three-column layout architecture and progressive disclosure patterns.

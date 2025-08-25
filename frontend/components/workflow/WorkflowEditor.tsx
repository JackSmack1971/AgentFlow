import React, { useCallback, useMemo, useRef, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  useReactFlow,
  ReactFlowProvider,
  BackgroundVariant,
  Panel
} from '@xyflow/react';
import type { Connection, Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import type { WorkflowNode, WorkflowEdge } from './types/workflow';
import { useWorkflowState, useWorkflowActions } from './hooks/useWorkflowState';
import WorkflowErrorBoundary from './WorkflowErrorBoundary';

// Import custom node types (we'll create these next)
import AgentNode from './NodeTypes/AgentNode';
import DataNode from './NodeTypes/DataNode';
import ActionNode from './NodeTypes/ActionNode';
import LogicNode from './NodeTypes/LogicNode';

// Node types mapping
const nodeTypes = {
  agentNode: AgentNode,
  dataNode: DataNode,
  actionNode: ActionNode,
  logicNode: LogicNode,
  inputNode: DataNode, // Reuse DataNode for input
  outputNode: DataNode // Reuse DataNode for output
};

interface WorkflowEditorProps {
  className?: string;
  readOnly?: boolean;
  showMiniMap?: boolean;
  showControls?: boolean;
  showBackground?: boolean;
  onNodeClick?: (node: WorkflowNode) => void;
  onEdgeClick?: (edge: WorkflowEdge) => void;
  onWorkflowChange?: (nodes: WorkflowNode[], edges: WorkflowEdge[]) => void;
}

// Main workflow editor component (internal)
function WorkflowEditorInternal({
  className = '',
  readOnly = false,
  showMiniMap = true,
  showControls = true,
  showBackground = true,
  onNodeClick,
  onEdgeClick,
  onWorkflowChange
}: WorkflowEditorProps) {
  // Get workflow state from Zustand
  const workflowState = useWorkflowState();
  const actions = useWorkflowActions();

  // Local React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState(workflowState.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(workflowState.edges);

  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { project } = useReactFlow();

  // Sync local state with global state
  useEffect(() => {
    setNodes(workflowState.nodes);
    setEdges(workflowState.edges);
  }, [workflowState.nodes, workflowState.edges, setNodes, setEdges]);

  // Notify parent of changes
  useEffect(() => {
    if (onWorkflowChange) {
      onWorkflowChange(nodes, edges);
    }
  }, [nodes, edges, onWorkflowChange]);

  // Handle connections
  const onConnect = useCallback((connection: Connection) => {
    if (readOnly) return;

    const success = actions.endConnection(connection);
    if (success) {
      // Update local edges state
      setEdges((eds) => addEdge({
        ...connection,
        id: `edge_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'default',
        data: { validationStatus: 'pending' }
      }, eds));
    }
  }, [actions, setEdges, readOnly]);

  // Handle node clicks
  const onNodeClickHandler = useCallback((event: React.MouseEvent, node: Node) => {
    if (readOnly) return;

    actions.selectNode(node.id);
    onNodeClick?.(node as WorkflowNode);
  }, [actions, onNodeClick, readOnly]);

  // Handle edge clicks
  const onEdgeClickHandler = useCallback((event: React.MouseEvent, edge: Edge) => {
    if (readOnly) return;

    actions.selectEdge(edge.id);
    onEdgeClick?.(edge as WorkflowEdge);
  }, [actions, onEdgeClick, readOnly]);

  // Handle drag over
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop (for drag-and-drop from palette)
  const onDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();

    if (readOnly || !reactFlowWrapper.current) return;

    const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
    const position = project({
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    });

    try {
      const nodeData = JSON.parse(event.dataTransfer.getData('application/json'));

      const newNode: Omit<WorkflowNode, 'id'> = {
        type: nodeData.type,
        position,
        data: nodeData.data,
        selected: false,
        dragging: false
      };

      actions.addNode(newNode);
    } catch (error) {
      console.error('Failed to parse dropped node data:', error);
    }
  }, [project, actions, readOnly]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (readOnly) return;

      // Delete selected nodes/edges
      if (event.key === 'Delete' || event.key === 'Backspace') {
        if (workflowState.selectedNodeId) {
          actions.removeNode(workflowState.selectedNodeId);
        }
        if (workflowState.selectedEdgeId) {
          actions.removeEdge(workflowState.selectedEdgeId);
        }
      }

      // Undo/Redo
      if (event.ctrlKey || event.metaKey) {
        if (event.key === 'z' && !event.shiftKey) {
          event.preventDefault();
          actions.undo();
        } else if ((event.key === 'y') || (event.key === 'z' && event.shiftKey)) {
          event.preventDefault();
          actions.redo();
        }

        // Duplicate selected node
        if (event.key === 'd' && workflowState.selectedNodeId) {
          event.preventDefault();
          actions.duplicateNode(workflowState.selectedNodeId);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [actions, workflowState.selectedNodeId, workflowState.selectedEdgeId, readOnly]);

  // Memoized background variant
  const backgroundVariant = useMemo(() => {
    return showBackground ? BackgroundVariant.Dots : undefined;
  }, [showBackground]);

  return (
    <div className={`w-full h-full ${className}`}>
      <div ref={reactFlowWrapper} className="w-full h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={readOnly ? undefined : onNodesChange}
          onEdgesChange={readOnly ? undefined : onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClickHandler}
          onEdgeClick={onEdgeClickHandler}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
          className="bg-gray-50"
          nodesDraggable={!readOnly}
          nodesConnectable={!readOnly}
          elementsSelectable={!readOnly}
          selectNodesOnDrag={false}
        >
          {/* Background */}
          {showBackground && backgroundVariant && (
            <Background
              variant={backgroundVariant}
              gap={20}
              size={1}
              color="#e5e7eb"
            />
          )}

          {/* Controls */}
          {showControls && (
            <Controls
              position="top-right"
              className="bg-white border border-gray-200 rounded shadow-sm"
            />
          )}

          {/* Mini Map */}
          {showMiniMap && (
            <MiniMap
              position="bottom-right"
              className="bg-white border border-gray-200 rounded shadow-sm"
              nodeColor="#3b82f6"
              maskColor="rgba(255, 255, 255, 0.2)"
            />
          )}

          {/* Status Panel */}
          <Panel position="top-left">
            <div className="bg-white border border-gray-200 rounded shadow-sm p-2 text-sm">
              <div className="flex items-center gap-4">
                <span>Nodes: {nodes.length}</span>
                <span>Edges: {edges.length}</span>
                {workflowState.isValidating && (
                  <span className="text-blue-600">Validating...</span>
                )}
                {workflowState.validationResult && (
                  <span className={workflowState.validationResult.isValid ? 'text-green-600' : 'text-red-600'}>
                    {workflowState.validationResult.isValid ? 'Valid' : 'Invalid'}
                  </span>
                )}
              </div>
            </div>
          </Panel>
        </ReactFlow>
      </div>

      {/* Loading overlay */}
      {workflowState.isLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <span className="text-gray-700">Loading workflow...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Main exported component with React Flow provider
export default function WorkflowEditor(props: WorkflowEditorProps) {
  return (
    <WorkflowErrorBoundary>
      <ReactFlowProvider>
        <WorkflowEditorInternal {...props} />
      </ReactFlowProvider>
    </WorkflowErrorBoundary>
  );
}

// Export internal component for testing
export { WorkflowEditorInternal };
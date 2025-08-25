import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type {
  WorkflowNode,
  WorkflowEdge,
  WorkflowDefinition,
  ValidationResult
} from '../types/workflow';
import { ValidationStatus } from '../types/workflow';
import type { Connection } from '@xyflow/react';

interface WorkflowState {
  // Core workflow data
  workflow: WorkflowDefinition;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];

  // UI state
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  isConnecting: boolean;
  connectionStart: { nodeId: string; handleId: string } | null;

  // Validation state
  validationResult: ValidationResult | null;
  isValidating: boolean;

  // History for undo/redo
  history: WorkflowDefinition[];
  historyIndex: number;

  // Performance state
  isLoading: boolean;
  performanceMode: boolean;

  // Actions
  addNode: (nodeData: Omit<WorkflowNode, 'id'>) => string;
  updateNode: (nodeId: string, updates: Partial<WorkflowNode>) => void;
  removeNode: (nodeId: string) => void;
  duplicateNode: (nodeId: string) => string;
  selectNode: (nodeId: string | null) => void;
  addEdge: (edgeData: Omit<WorkflowEdge, 'id'>) => string;
  updateEdge: (edgeId: string, updates: Partial<WorkflowEdge>) => void;
  removeEdge: (edgeId: string) => void;
  selectEdge: (edgeId: string | null) => void;
  startConnection: (nodeId: string, handleId: string) => void;
  endConnection: (connection: Connection) => boolean;
  cancelConnection: () => void;
  createWorkflow: (name: string, description?: string) => void;
  loadWorkflow: (workflow: WorkflowDefinition) => void;
  saveWorkflow: () => WorkflowDefinition;
  resetWorkflow: () => void;
  validateWorkflow: () => Promise<ValidationResult>;
  clearValidation: () => void;
  undo: () => boolean;
  redo: () => boolean;
  canUndo: () => boolean;
  canRedo: () => boolean;
  clearHistory: () => void;
  setPerformanceMode: (enabled: boolean) => void;
  setLoading: (loading: boolean) => void;
  getNodeById: (nodeId: string) => WorkflowNode | undefined;
  getEdgeById: (edgeId: string) => WorkflowEdge | undefined;
  getConnectedNodes: (nodeId: string) => WorkflowNode[];
  getNodeConnections: (nodeId: string) => { incoming: WorkflowEdge[], outgoing: WorkflowEdge[] };
  exportWorkflow: () => string;
  importWorkflow: (jsonString: string) => boolean;
}

const initialWorkflow: WorkflowDefinition = {
  id: 'new-workflow',
  name: 'New Workflow',
  version: '1.0.0',
  nodes: [],
  edges: [],
  metadata: {
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }
};

export const useWorkflowState = create<WorkflowState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        workflow: initialWorkflow,
        nodes: [],
        edges: [],
        selectedNodeId: null,
        selectedEdgeId: null,
        isConnecting: false,
        connectionStart: null,
        validationResult: null,
        isValidating: false,
        history: [initialWorkflow],
        historyIndex: 0,
        isLoading: false,
        performanceMode: false,

        // Actions
        addNode: (nodeData) => {
          const state = get();
          const newNode: WorkflowNode = {
            ...nodeData,
            id: `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            selected: false,
            dragging: false
          };

          set((state) => ({
            nodes: [...state.nodes, newNode],
            workflow: {
              ...state.workflow,
              nodes: [...state.workflow.nodes, newNode],
              metadata: {
                ...state.workflow.metadata,
                updatedAt: new Date().toISOString()
              }
            }
          }));

          return newNode.id;
        },

        updateNode: (nodeId, updates) => {
          const state = get();
          const nodeIndex = state.nodes.findIndex(n => n.id === nodeId);
          if (nodeIndex === -1) return;

          const newNodes = [...state.nodes];
          newNodes[nodeIndex] = { ...newNodes[nodeIndex], ...updates };

          set((state) => ({
            nodes: newNodes,
            workflow: {
              ...state.workflow,
              nodes: newNodes,
              metadata: {
                ...state.workflow.metadata,
                updatedAt: new Date().toISOString()
              }
            }
          }));
        },

        removeNode: (nodeId) => {
          const state = get();
          const newNodes = state.nodes.filter(n => n.id !== nodeId);
          const newEdges = state.edges.filter(e => e.source !== nodeId && e.target !== nodeId);

          set((state) => ({
            nodes: newNodes,
            edges: newEdges,
            selectedNodeId: state.selectedNodeId === nodeId ? null : state.selectedNodeId,
            workflow: {
              ...state.workflow,
              nodes: newNodes,
              edges: newEdges,
              metadata: {
                ...state.workflow.metadata,
                updatedAt: new Date().toISOString()
              }
            }
          }));
        },

        duplicateNode: (nodeId) => {
          const state = get();
          const nodeToDuplicate = state.nodes.find(n => n.id === nodeId);
          if (!nodeToDuplicate) return nodeId;

          const duplicatedNode: WorkflowNode = {
            ...nodeToDuplicate,
            id: `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            position: {
              x: nodeToDuplicate.position.x + 50,
              y: nodeToDuplicate.position.y + 50
            },
            selected: false,
            dragging: false,
            data: {
              ...nodeToDuplicate.data,
              label: `${nodeToDuplicate.data.label} (Copy)`
            }
          };

          set((state) => ({
            nodes: [...state.nodes, duplicatedNode],
            workflow: {
              ...state.workflow,
              nodes: [...state.workflow.nodes, duplicatedNode],
              metadata: {
                ...state.workflow.metadata,
                updatedAt: new Date().toISOString()
              }
            }
          }));

          return duplicatedNode.id;
        },

        selectNode: (nodeId) => {
          set({ selectedNodeId: nodeId });
        },

        addEdge: (edgeData) => {
          const state = get();
          const newEdge: WorkflowEdge = {
            ...edgeData,
            id: `edge_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type: edgeData.type || 'default',
            data: {
              validationStatus: ValidationStatus.PENDING,
              ...edgeData.data
            }
          };

          set((state) => ({
            edges: [...state.edges, newEdge],
            workflow: {
              ...state.workflow,
              edges: [...state.workflow.edges, newEdge],
              metadata: {
                ...state.workflow.metadata,
                updatedAt: new Date().toISOString()
              }
            }
          }));

          return newEdge.id;
        },

        updateEdge: (edgeId, updates) => {
          const state = get();
          const edgeIndex = state.edges.findIndex(e => e.id === edgeId);
          if (edgeIndex === -1) return;

          const newEdges = [...state.edges];
          newEdges[edgeIndex] = { ...newEdges[edgeIndex], ...updates };

          set((state) => ({
            edges: newEdges,
            workflow: {
              ...state.workflow,
              edges: newEdges,
              metadata: {
                ...state.workflow.metadata,
                updatedAt: new Date().toISOString()
              }
            }
          }));
        },

        removeEdge: (edgeId) => {
          const state = get();
          const newEdges = state.edges.filter(e => e.id !== edgeId);

          set((state) => ({
            edges: newEdges,
            selectedEdgeId: state.selectedEdgeId === edgeId ? null : state.selectedEdgeId,
            workflow: {
              ...state.workflow,
              edges: newEdges,
              metadata: {
                ...state.workflow.metadata,
                updatedAt: new Date().toISOString()
              }
            }
          }));
        },

        selectEdge: (edgeId) => {
          set({ selectedEdgeId: edgeId });
        },

        startConnection: (nodeId, handleId) => {
          set({
            isConnecting: true,
            connectionStart: { nodeId, handleId }
          });
        },

        endConnection: (connection) => {
          const state = get();
          if (!state.connectionStart) return false;

          const sourceNode = state.nodes.find(n => n.id === connection.source);
          const targetNode = state.nodes.find(n => n.id === connection.target);

          if (!sourceNode || !targetNode) return false;

          const newEdge = {
            source: connection.source,
            target: connection.target,
            sourceHandle: connection.sourceHandle || undefined,
            targetHandle: connection.targetHandle || undefined,
            type: 'default',
            data: {
              validationStatus: ValidationStatus.PENDING
            }
          };

          get().addEdge(newEdge);

          set({
            isConnecting: false,
            connectionStart: null
          });

          return true;
        },

        cancelConnection: () => {
          set({
            isConnecting: false,
            connectionStart: null
          });
        },

        createWorkflow: (name, description = '') => {
          const newWorkflow: WorkflowDefinition = {
            id: `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            name,
            description,
            version: '1.0.0',
            nodes: [],
            edges: [],
            metadata: {
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString()
            }
          };

          set({
            workflow: newWorkflow,
            nodes: [],
            edges: [],
            selectedNodeId: null,
            selectedEdgeId: null,
            validationResult: null,
            history: [newWorkflow],
            historyIndex: 0
          });
        },

        loadWorkflow: (workflow) => {
          set({
            workflow,
            nodes: workflow.nodes,
            edges: workflow.edges,
            selectedNodeId: null,
            selectedEdgeId: null,
            validationResult: null,
            history: [workflow],
            historyIndex: 0
          });
        },

        saveWorkflow: () => {
          const state = get();
          return {
            ...state.workflow,
            metadata: {
              ...state.workflow.metadata,
              updatedAt: new Date().toISOString()
            }
          };
        },

        resetWorkflow: () => {
          set({
            workflow: initialWorkflow,
            nodes: [],
            edges: [],
            selectedNodeId: null,
            selectedEdgeId: null,
            validationResult: null,
            history: [initialWorkflow],
            historyIndex: 0
          });
        },

        validateWorkflow: async () => {
          const state = get();
          set({ isValidating: true });

          try {
            const errors: any[] = [];
            const warnings: any[] = [];

            const connectedNodeIds = new Set([
              ...state.edges.map(e => e.source),
              ...state.edges.map(e => e.target)
            ]);

            state.nodes.forEach(node => {
              if (!connectedNodeIds.has(node.id)) {
                warnings.push({
                  nodeId: node.id,
                  type: 'unused_node',
                  message: `Node "${node.data.label}" is not connected to any other nodes`,
                  severity: 'warning'
                });
              }
            });

            const result: ValidationResult = {
              isValid: errors.length === 0,
              errors,
              warnings
            };

            set({ validationResult: result });
            return result;
          } finally {
            set({ isValidating: false });
          }
        },

        clearValidation: () => {
          set({ validationResult: null });
        },

        undo: () => {
          const state = get();
          if (state.historyIndex <= 0) return false;

          const previousWorkflow = state.history[state.historyIndex - 1];
          if (!previousWorkflow) return false;

          set({
            workflow: previousWorkflow,
            nodes: previousWorkflow.nodes,
            edges: previousWorkflow.edges,
            historyIndex: state.historyIndex - 1
          });

          return true;
        },

        redo: () => {
          const state = get();
          if (state.historyIndex >= state.history.length - 1) return false;

          const nextWorkflow = state.history[state.historyIndex + 1];
          if (!nextWorkflow) return false;

          set({
            workflow: nextWorkflow,
            nodes: nextWorkflow.nodes,
            edges: nextWorkflow.edges,
            historyIndex: state.historyIndex + 1
          });

          return true;
        },

        canUndo: () => {
          const state = get();
          return state.historyIndex > 0;
        },

        canRedo: () => {
          const state = get();
          return state.historyIndex < state.history.length - 1;
        },

        clearHistory: () => {
          const state = get();
          set({
            history: [state.workflow],
            historyIndex: 0
          });
        },

        setPerformanceMode: (enabled) => {
          set({ performanceMode: enabled });
        },

        setLoading: (loading) => {
          set({ isLoading: loading });
        },

        getNodeById: (nodeId) => {
          const state = get();
          return state.nodes.find(n => n.id === nodeId);
        },

        getEdgeById: (edgeId) => {
          const state = get();
          return state.edges.find(e => e.id === edgeId);
        },

        getConnectedNodes: (nodeId) => {
          const state = get();
          const connectedNodeIds = new Set([
            ...state.edges.filter(e => e.source === nodeId).map(e => e.target),
            ...state.edges.filter(e => e.target === nodeId).map(e => e.source)
          ]);

          return state.nodes.filter(n => connectedNodeIds.has(n.id));
        },

        getNodeConnections: (nodeId) => {
          const state = get();
          const incoming = state.edges.filter(e => e.target === nodeId);
          const outgoing = state.edges.filter(e => e.source === nodeId);

          return { incoming, outgoing };
        },

        exportWorkflow: () => {
          const state = get();
          return JSON.stringify(state.workflow, null, 2);
        },

        importWorkflow: (jsonString) => {
          try {
            const workflow: WorkflowDefinition = JSON.parse(jsonString);
            get().loadWorkflow(workflow);
            return true;
          } catch (error) {
            console.error('Failed to import workflow:', error);
            return false;
          }
        }
      }),
      {
        name: 'workflow-storage',
        partialize: (state) => ({
          workflow: state.workflow,
          nodes: state.nodes,
          edges: state.edges
        })
      }
    ),
    {
      name: 'workflow-store'
    }
  )
);

// Selector hooks for better performance
export const useWorkflowNodes = () => useWorkflowState((state) => state.nodes);
export const useWorkflowEdges = () => useWorkflowState((state) => state.edges);
export const useSelectedNode = () => useWorkflowState((state) => state.selectedNodeId);
export const useSelectedEdge = () => useWorkflowState((state) => state.selectedEdgeId);
export const useValidationResult = () => useWorkflowState((state) => state.validationResult);
export const useWorkflowActions = () => useWorkflowState((state) => ({
  addNode: state.addNode,
  updateNode: state.updateNode,
  removeNode: state.removeNode,
  duplicateNode: state.duplicateNode,
  selectNode: state.selectNode,
  addEdge: state.addEdge,
  updateEdge: state.updateEdge,
  removeEdge: state.removeEdge,
  selectEdge: state.selectEdge,
  startConnection: state.startConnection,
  endConnection: state.endConnection,
  cancelConnection: state.cancelConnection,
  createWorkflow: state.createWorkflow,
  loadWorkflow: state.loadWorkflow,
  saveWorkflow: state.saveWorkflow,
  resetWorkflow: state.resetWorkflow,
  validateWorkflow: state.validateWorkflow,
  clearValidation: state.clearValidation,
  undo: state.undo,
  redo: state.redo,
  canUndo: state.canUndo,
  canRedo: state.canRedo,
  clearHistory: state.clearHistory,
  setPerformanceMode: state.setPerformanceMode,
  setLoading: state.setLoading,
  getNodeById: state.getNodeById,
  getEdgeById: state.getEdgeById,
  getConnectedNodes: state.getConnectedNodes,
  getNodeConnections: state.getNodeConnections,
  exportWorkflow: state.exportWorkflow,
  importWorkflow: state.importWorkflow
}));
export const useWorkflowHistory = () => useWorkflowState((state) => ({
  canUndo: state.canUndo(),
  canRedo: state.canRedo(),
  undo: state.undo,
  redo: state.redo
}));

export default useWorkflowState;
import type { NodeProps } from '@xyflow/react';
import type { NodeData, WorkflowNode } from './workflow';

// Base node component props
export interface BaseNodeProps extends NodeProps {
  data: NodeData;
}

// Agent node props
export interface AgentNodeProps extends BaseNodeProps {
  data: import('./workflow').AgentNodeData;
}

// Data node props
export interface DataNodeProps extends BaseNodeProps {
  data: import('./workflow').DataNodeData;
}

// Action node props
export interface ActionNodeProps extends BaseNodeProps {
  data: import('./workflow').ActionNodeData;
}

// Logic node props
export interface LogicNodeProps extends BaseNodeProps {
  data: import('./workflow').LogicNodeData;
}

// Node component mapping
export interface NodeComponentMap {
  agentNode: React.ComponentType<AgentNodeProps>;
  dataNode: React.ComponentType<DataNodeProps>;
  actionNode: React.ComponentType<ActionNodeProps>;
  logicNode: React.ComponentType<LogicNodeProps>;
  inputNode: React.ComponentType<BaseNodeProps>;
  outputNode: React.ComponentType<BaseNodeProps>;
}

// Node configuration
export interface NodeConfig {
  icon: string;
  color: string;
  category: string;
  description: string;
  defaultData: Partial<NodeData>;
  minInputs?: number;
  maxInputs?: number;
  minOutputs?: number;
  maxOutputs?: number;
}

// Node configurations for each type
export const NODE_CONFIGS: Record<string, NodeConfig> = {
  agentNode: {
    icon: '🤖',
    color: '#3B82F6',
    category: 'Agent',
    description: 'AI agent for processing and generating content',
    defaultData: {
      label: 'Agent',
      category: 'agent' as const,
      agentType: 'chat' as const,
      model: 'gpt-4',
      temperature: 0.7,
      maxTokens: 1000
    },
    minInputs: 1,
    maxInputs: 5,
    minOutputs: 1,
    maxOutputs: 3
  },
  dataNode: {
    icon: '📊',
    color: '#10B981',
    category: 'Data',
    description: 'Data processing and transformation',
    defaultData: {
      label: 'Data Processor',
      category: 'data' as const,
      dataType: 'object' as const
    },
    minInputs: 1,
    maxInputs: 10,
    minOutputs: 1,
    maxOutputs: 10
  },
  actionNode: {
    icon: '⚡',
    color: '#F59E0B',
    category: 'Action',
    description: 'Execute external actions and API calls',
    defaultData: {
      label: 'Action',
      category: 'action' as const,
      actionType: 'http_request' as const,
      timeout: 30000,
      retries: 3
    },
    minInputs: 0,
    maxInputs: 5,
    minOutputs: 1,
    maxOutputs: 3
  },
  logicNode: {
    icon: '🔀',
    color: '#8B5CF6',
    category: 'Logic',
    description: 'Control flow and decision making',
    defaultData: {
      label: 'Logic',
      category: 'logic' as const,
      logicType: 'condition' as const
    },
    minInputs: 1,
    maxInputs: 5,
    minOutputs: 1,
    maxOutputs: 5
  },
  inputNode: {
    icon: '📥',
    color: '#6B7280',
    category: 'Input',
    description: 'Workflow input node',
    defaultData: {
      label: 'Input',
      category: 'input' as const
    },
    minInputs: 0,
    maxInputs: 0,
    minOutputs: 1,
    maxOutputs: 10
  },
  outputNode: {
    icon: '📤',
    color: '#6B7280',
    category: 'Output',
    description: 'Workflow output node',
    defaultData: {
      label: 'Output',
      category: 'output' as const
    },
    minInputs: 1,
    maxInputs: 10,
    minOutputs: 0,
    maxOutputs: 0
  }
};

// Node creation helper
export interface CreateNodeOptions {
  type: string;
  position: { x: number; y: number };
  data?: Partial<NodeData>;
}

export function createNode(options: CreateNodeOptions): WorkflowNode {
  const config = NODE_CONFIGS[options.type];
  if (!config) {
    throw new Error(`Unknown node type: ${options.type}`);
  }

  return {
    id: `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    type: options.type,
    position: options.position,
    data: {
      ...config.defaultData,
      ...options.data
    } as NodeData,
    selected: false,
    dragging: false
  };
}

// Node validation helpers
export interface NodeValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export function validateNodeConnections(
  node: WorkflowNode,
  connectedNodes: WorkflowNode[],
  edges: import('./workflow').WorkflowEdge[]
): NodeValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const config = NODE_CONFIGS[node.type];

  if (!config) {
    errors.push(`Unknown node type: ${node.type}`);
    return { isValid: false, errors, warnings };
  }

  // Check input connections
  const inputEdges = edges.filter(edge => edge.target === node.id);
  if (config.minInputs !== undefined && inputEdges.length < config.minInputs) {
    errors.push(`Node requires at least ${config.minInputs} input connections`);
  }
  if (config.maxInputs !== undefined && inputEdges.length > config.maxInputs) {
    errors.push(`Node can have at most ${config.maxInputs} input connections`);
  }

  // Check output connections
  const outputEdges = edges.filter(edge => edge.source === node.id);
  if (config.minOutputs !== undefined && outputEdges.length < config.minOutputs) {
    errors.push(`Node requires at least ${config.minOutputs} output connections`);
  }
  if (config.maxOutputs !== undefined && outputEdges.length > config.maxOutputs) {
    errors.push(`Node can have at most ${config.maxOutputs} output connections`);
  }

  // Validate node-specific data
  const data = node.data;

  // Agent node validation
  if (node.type === 'agentNode') {
    const agentData = data as import('./workflow').AgentNodeData;
    if (!agentData.model) {
      errors.push('Agent node must specify a model');
    }
    if (agentData.temperature !== undefined && (agentData.temperature < 0 || agentData.temperature > 2)) {
      errors.push('Agent temperature must be between 0 and 2');
    }
  }

  // Action node validation
  if (node.type === 'actionNode') {
    const actionData = data as import('./workflow').ActionNodeData;
    if (!actionData.actionType) {
      errors.push('Action node must specify an action type');
    }
    if (actionData.timeout !== undefined && actionData.timeout < 1000) {
      warnings.push('Action timeout seems very low (< 1 second)');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
}
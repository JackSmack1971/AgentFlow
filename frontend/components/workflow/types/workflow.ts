import type { Node, Edge, NodeTypes, EdgeTypes } from '@xyflow/react';

// Base node data interface
export interface BaseNodeData extends Record<string, unknown> {
  id: string;
  label: string;
  description?: string;
  category: NodeCategory;
  inputs?: NodePort[];
  outputs?: NodePort[];
  config?: Record<string, any>;
  validationErrors?: string[];
  isValid?: boolean;
}

// Node port interface for connections
export interface NodePort {
  id: string;
  label: string;
  type: PortType;
  required?: boolean;
  dataType?: DataType;
  description?: string;
}

// Node categories
export enum NodeCategory {
  AGENT = 'agent',
  DATA = 'data',
  ACTION = 'action',
  LOGIC = 'logic',
  INPUT = 'input',
  OUTPUT = 'output'
}

// Port types
export enum PortType {
  INPUT = 'input',
  OUTPUT = 'output'
}

// Data types for ports
export enum DataType {
  STRING = 'string',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  OBJECT = 'object',
  ARRAY = 'array',
  FILE = 'file',
  IMAGE = 'image',
  AUDIO = 'audio',
  VIDEO = 'video',
  ANY = 'any'
}

// Agent node data
export interface AgentNodeData extends BaseNodeData {
  category: NodeCategory.AGENT;
  agentType: AgentType;
  model?: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
  tools?: string[];
}

// Data node data
export interface DataNodeData extends BaseNodeData {
  category: NodeCategory.DATA;
  dataType: DataType;
  source?: DataSource;
  schema?: Record<string, any>;
  sampleData?: any;
}

// Action node data
export interface ActionNodeData extends BaseNodeData {
  category: NodeCategory.ACTION;
  actionType: ActionType;
  parameters?: Record<string, any>;
  timeout?: number;
  retries?: number;
}

// Logic node data
export interface LogicNodeData extends BaseNodeData {
  category: NodeCategory.LOGIC;
  logicType: LogicType;
  condition?: string;
  branches?: string[];
}

// Agent types
export enum AgentType {
  CHAT = 'chat',
  REASONING = 'reasoning',
  CODE_GENERATOR = 'code_generator',
  DATA_ANALYZER = 'data_analyzer',
  IMAGE_GENERATOR = 'image_generator',
  CUSTOM = 'custom'
}

// Data sources
export enum DataSource {
  API = 'api',
  DATABASE = 'database',
  FILE = 'file',
  STREAM = 'stream',
  MANUAL = 'manual'
}

// Action types
export enum ActionType {
  HTTP_REQUEST = 'http_request',
  DATABASE_QUERY = 'database_query',
  FILE_OPERATION = 'file_operation',
  EMAIL = 'email',
  NOTIFICATION = 'notification',
  CUSTOM = 'custom'
}

// Logic types
export enum LogicType {
  CONDITION = 'condition',
  LOOP = 'loop',
  SWITCH = 'switch',
  MERGE = 'merge',
  SPLIT = 'split'
}

// Union type for all node data
export type NodeData = AgentNodeData | DataNodeData | ActionNodeData | LogicNodeData;

// Workflow node with React Flow types
export interface WorkflowNode extends Node {
  type: string;
  data: NodeData;
  position: { x: number; y: number };
  selected?: boolean;
  dragging?: boolean;
}

// Workflow edge with validation
export interface WorkflowEdge extends Edge {
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  type?: string;
  data?: {
    validationStatus?: ValidationStatus;
    errorMessage?: string;
  };
}

// Validation status
export enum ValidationStatus {
  VALID = 'valid',
  INVALID = 'invalid',
  WARNING = 'warning',
  PENDING = 'pending'
}

// Workflow definition
export interface WorkflowDefinition {
  id: string;
  name: string;
  description?: string;
  version: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  metadata?: {
    author?: string;
    createdAt?: string;
    updatedAt?: string;
    tags?: string[];
  };
  settings?: WorkflowSettings;
}

// Workflow settings
export interface WorkflowSettings {
  maxExecutionTime?: number;
  maxRetries?: number;
  errorHandling?: ErrorHandlingStrategy;
  logging?: LoggingConfiguration;
  security?: SecuritySettings;
}

// Error handling strategies
export enum ErrorHandlingStrategy {
  STOP_ON_ERROR = 'stop_on_error',
  CONTINUE_ON_ERROR = 'continue_on_error',
  RETRY_ON_ERROR = 'retry_on_error'
}

// Logging configuration
export interface LoggingConfiguration {
  level: LogLevel;
  includeTimestamps: boolean;
  includeNodeOutputs: boolean;
  maxLogSize?: number;
}

// Log levels
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error'
}

// Security settings
export interface SecuritySettings {
  enableEncryption: boolean;
  allowedDomains?: string[];
  maxFileSize?: number;
  timeoutSettings?: TimeoutSettings;
}

// Timeout settings
export interface TimeoutSettings {
  nodeExecutionTimeout: number;
  workflowExecutionTimeout: number;
  apiRequestTimeout: number;
}

// Node type mapping
export const NODE_TYPES: Record<NodeCategory, string> = {
  [NodeCategory.AGENT]: 'agentNode',
  [NodeCategory.DATA]: 'dataNode',
  [NodeCategory.ACTION]: 'actionNode',
  [NodeCategory.LOGIC]: 'logicNode',
  [NodeCategory.INPUT]: 'inputNode',
  [NodeCategory.OUTPUT]: 'outputNode'
};

// Edge type mapping
export const EDGE_TYPES = {
  DEFAULT: 'default',
  VALID: 'valid',
  INVALID: 'invalid',
  WARNING: 'warning'
} as const;

// Validation result
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

// Validation error
export interface ValidationError {
  nodeId?: string;
  edgeId?: string;
  type: ValidationErrorType;
  message: string;
  severity: 'error' | 'warning';
}

// Validation warning
export interface ValidationWarning {
  nodeId?: string;
  edgeId?: string;
  type: ValidationWarningType;
  message: string;
}

// Validation error types
export enum ValidationErrorType {
  MISSING_CONNECTION = 'missing_connection',
  INVALID_CONNECTION = 'invalid_connection',
  MISSING_CONFIG = 'missing_config',
  INVALID_CONFIG = 'invalid_config',
  CYCLIC_DEPENDENCY = 'cyclic_dependency',
  TYPE_MISMATCH = 'type_mismatch'
}

// Validation warning types
export enum ValidationWarningType {
  UNUSED_NODE = 'unused_node',
  PERFORMANCE_ISSUE = 'performance_issue',
  SECURITY_CONCERN = 'security_concern'
}

// Workflow execution context
export interface WorkflowExecutionContext {
  workflowId: string;
  executionId: string;
  variables: Record<string, any>;
  secrets: Record<string, string>;
  startTime: Date;
  timeout: number;
  maxRetries: number;
}

// Node execution result
export interface NodeExecutionResult {
  nodeId: string;
  success: boolean;
  output?: any;
  error?: string;
  executionTime: number;
  retries: number;
  logs?: string[];
}

// Workflow execution result
export interface WorkflowExecutionResult {
  executionId: string;
  success: boolean;
  results: NodeExecutionResult[];
  totalExecutionTime: number;
  error?: string;
  logs?: string[];
}
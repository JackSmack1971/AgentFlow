import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import BaseNode from './BaseNode';
import type { AgentNodeData } from '../types/workflow';

interface AgentNodeProps extends NodeProps {
  data: AgentNodeData;
}

const AgentNode = memo(({ data }: AgentNodeProps) => {
  return React.createElement(BaseNode, {
    data,
    icon: '🤖',
    color: '#3B82F6',
    children: React.createElement(
      'div',
      { className: 'space-y-1' },
      [
        data.agentType && React.createElement(
          'div',
          { key: 'type', className: 'text-xs text-gray-500' },
          `Type: ${data.agentType}`
        ),
        data.model && React.createElement(
          'div',
          { key: 'model', className: 'text-xs text-gray-500' },
          `Model: ${data.model}`
        ),
        data.temperature !== undefined && React.createElement(
          'div',
          { key: 'temp', className: 'text-xs text-gray-500' },
          `Temp: ${data.temperature}`
        )
      ].filter(Boolean)
    )
  });
});

AgentNode.displayName = 'AgentNode';

export default AgentNode;
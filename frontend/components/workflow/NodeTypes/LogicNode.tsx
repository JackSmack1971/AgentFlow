import React, { memo } from 'react';
import BaseNode from './BaseNode';
import type { NodeProps } from '@xyflow/react';
import type { LogicNodeData } from '../types/workflow';

interface LogicNodeProps extends NodeProps {
  data: LogicNodeData;
}

const LogicNode = memo(({ data }: LogicNodeProps) => {
  return React.createElement(BaseNode, {
    data,
    icon: '🔀',
    color: '#8B5CF6'
  });
});

LogicNode.displayName = 'LogicNode';

export default LogicNode;
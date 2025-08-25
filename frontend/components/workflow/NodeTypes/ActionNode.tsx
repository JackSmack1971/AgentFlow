import React, { memo } from 'react';
import BaseNode from './BaseNode';
import type { NodeProps } from '@xyflow/react';
import type { ActionNodeData } from '../types/workflow';

interface ActionNodeProps extends NodeProps {
  data: ActionNodeData;
}

const ActionNode = memo(({ data }: ActionNodeProps) => {
  return React.createElement(BaseNode, {
    data,
    icon: '⚡',
    color: '#F59E0B'
  });
});

ActionNode.displayName = 'ActionNode';

export default ActionNode;
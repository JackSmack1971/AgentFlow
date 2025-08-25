import React, { memo } from 'react';
import BaseNode from './BaseNode';
import type { NodeProps } from '@xyflow/react';
import type { DataNodeData } from '../types/workflow';

interface DataNodeProps extends NodeProps {
  data: DataNodeData;
}

const DataNode = memo(({ data }: DataNodeProps) => {
  return React.createElement(BaseNode, {
    data,
    icon: '📊',
    color: '#10B981'
  });
});

DataNode.displayName = 'DataNode';

export default DataNode;
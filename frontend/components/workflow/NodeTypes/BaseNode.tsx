import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import type { NodeData } from '../types/workflow';

interface BaseNodeProps extends NodeProps {
  data: NodeData;
  icon?: string;
  color?: string;
  children?: React.ReactNode;
}

const BaseNode = memo(({ data, icon, color = '#6B7280', children }: BaseNodeProps) => {
  return React.createElement(
    'div',
    {
      className: `px-4 py-3 shadow-md rounded-md bg-white border-2 min-w-[150px]`,
      style: { borderColor: color }
    },
    [
      // Node Header
      React.createElement(
        'div',
        {
          key: 'header',
          className: 'flex items-center gap-2 mb-2'
        },
        [
          icon && React.createElement(
            'span',
            {
              key: 'icon',
              className: 'text-lg',
              role: 'img',
              'aria-label': data.category
            },
            icon
          ),
          React.createElement(
            'div',
            {
              key: 'label',
              className: 'font-medium text-gray-800 truncate'
            },
            data.label
          )
        ].filter(Boolean)
      ),

      // Node Content
      children && React.createElement(
        'div',
        {
          key: 'content',
          className: 'text-sm text-gray-600'
        },
        children
      ),

      // Input Handle
      React.createElement(
        Handle,
        {
          key: 'input',
          type: 'target',
          position: Position.Left,
          className: '!bg-blue-500 !border-blue-500 !w-3 !h-3'
        }
      ),

      // Output Handle
      React.createElement(
        Handle,
        {
          key: 'output',
          type: 'source',
          position: Position.Right,
          className: '!bg-green-500 !border-green-500 !w-3 !h-3'
        }
      )
    ].filter(Boolean)
  );
});

BaseNode.displayName = 'BaseNode';

export default BaseNode;
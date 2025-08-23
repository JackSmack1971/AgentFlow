// biome-ignore lint/correctness/noUnusedImports: React import required for JSX
import React from 'react';
import KnowledgeItem, { type KnowledgeItemProps } from './knowledge-item.tsx';

interface KnowledgeListProps {
  items: KnowledgeItemProps[];
}

export default function KnowledgeList({
  items,
}: KnowledgeListProps): JSX.Element {
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <KnowledgeItem key={item.id} {...item} />
      ))}
    </ul>
  );
}

export type { KnowledgeListProps };

// biome-ignore lint/correctness/noUnusedImports: React import required for JSX
import React from 'react';

interface KnowledgeItemProps {
  id: string;
  title: string;
}

export default function KnowledgeItem({
  id,
  title,
}: KnowledgeItemProps): JSX.Element {
  return (
    <li id={id} className="p-2 border">
      {title}
    </li>
  );
}

export type { KnowledgeItemProps };

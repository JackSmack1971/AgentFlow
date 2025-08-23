// biome-ignore lint/correctness/noUnusedImports: React import required for JSX
import React from 'react';
import type { KnowledgeItemProps } from '../../../components/knowledge/knowledge-item.tsx';
import KnowledgeList from '../../../components/knowledge/knowledge-list.tsx';

class KnowledgeFetchError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'KnowledgeFetchError';
  }
}

async function fetchKnowledge(): Promise<KnowledgeItemProps[]> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (typeof baseUrl !== 'string' || !baseUrl) {
    throw new KnowledgeFetchError('API base URL missing');
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  const url = `${baseUrl}/knowledge`;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const res = await fetch(url, { signal: controller.signal });
      if (!res.ok) {
        throw new KnowledgeFetchError(`Request failed: ${res.status}`);
      }
      const data = (await res.json()) as unknown;
      if (!Array.isArray(data)) {
        throw new KnowledgeFetchError('Invalid response');
      }
      clearTimeout(timeout);
      return data.map((d) => ({
        id: String((d as { id: unknown }).id),
        title: String((d as { title: unknown }).title),
      }));
    } catch (error) {
      if (attempt === 2) {
        const message =
          error instanceof Error ? error.message : 'Unknown error';
        throw new KnowledgeFetchError(message);
      }
    }
  }
  throw new KnowledgeFetchError('Failed to fetch knowledge');
}

export default async function KnowledgePage(): Promise<JSX.Element> {
  let items: KnowledgeItemProps[] = [];
  try {
    items = await fetchKnowledge();
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error(new KnowledgeFetchError(message));
  }
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-xl font-semibold">Knowledge</h1>
      <KnowledgeList items={items} />
    </div>
  );
}

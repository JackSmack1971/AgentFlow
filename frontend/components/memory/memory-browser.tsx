'use client';

import React, { useEffect, useState } from 'react';
import { z } from 'zod';
import ApiClient from '../../lib/api.ts';
import type { MemoryItem } from '../../lib/types.ts';

class MemoryBrowserError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'MemoryBrowserError';
  }
}

const searchSchema = z.object({ q: z.string().optional() });
const textSchema = z.object({ text: z.string().min(1) });

async function loadItems(
  client: ApiClient,
  q: string,
  setItems: React.Dispatch<React.SetStateAction<MemoryItem[]>>,
  setError: React.Dispatch<React.SetStateAction<string | null>>,
): Promise<void> {
  try {
    const data = q ? await client.searchMemoryItems({ q }) : await client.listMemoryItems();
    setItems(data);
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Load failed';
    setError(new MemoryBrowserError(msg).message);
  }
}

async function editItem(
  client: ApiClient,
  id: string,
  refresh: () => Promise<void>,
  setError: React.Dispatch<React.SetStateAction<string | null>>,
): Promise<void> {
  const input = prompt('New text');
  if (input === null) return;
  try {
    const { text } = textSchema.parse({ text: input });
    await client.updateMemoryItem(id, { text });
    await refresh();
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Update failed';
    setError(new MemoryBrowserError(msg).message);
  }
}

async function removeItem(
  client: ApiClient,
  id: string,
  refresh: () => Promise<void>,
  setError: React.Dispatch<React.SetStateAction<string | null>>,
): Promise<void> {
  try {
    await client.deleteMemoryItem(id);
    await refresh();
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Delete failed';
    setError(new MemoryBrowserError(msg).message);
  }
}

async function searchItems(
  e: React.FormEvent,
  q: string,
  setQ: React.Dispatch<React.SetStateAction<string>>,
  client: ApiClient,
  setItems: React.Dispatch<React.SetStateAction<MemoryItem[]>>,
  setError: React.Dispatch<React.SetStateAction<string | null>>,
): Promise<void> {
  e.preventDefault();
  try {
    const { q: query } = searchSchema.parse({ q });
    setQ(query ?? '');
    await loadItems(client, query ?? '', setItems, setError);
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Search failed';
    setError(new MemoryBrowserError(msg).message);
  }
}

function renderItem(
  item: MemoryItem,
  client: ApiClient,
  refresh: () => Promise<void>,
  setError: React.Dispatch<React.SetStateAction<string | null>>,
): JSX.Element {
  return (
    <li key={item.id} className="flex gap-2">
      <span className="flex-1">{item.text}</span>
      <button
        type="button"
        className="text-blue-600"
        onClick={() => editItem(client, item.id!, refresh, setError)}
      >
        Edit
      </button>
      <button
        type="button"
        className="text-red-600"
        onClick={() => removeItem(client, item.id!, refresh, setError)}
      >
        Delete
      </button>
    </li>
  );
}

function SearchForm({
  q,
  setQ,
  onSearch,
}: {
  q: string;
  setQ: React.Dispatch<React.SetStateAction<string>>;
  onSearch: (e: React.FormEvent) => void;
}): JSX.Element {
  return (
    <form onSubmit={onSearch} className="flex gap-2">
      <input
        aria-label="Search"
        className="border p-2"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <button type="submit" className="bg-blue-500 px-3 py-2 text-white">
        Search
      </button>
    </form>
  );
}

export default function MemoryBrowser(): JSX.Element {
  const client = new ApiClient();
  const [q, setQ] = useState('');
  const [items, setItems] = useState<MemoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const refresh = async () => loadItems(client, q, setItems, setError);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, [q]);

  return (
    <div className="space-y-4">
      <SearchForm
        q={q}
        setQ={setQ}
        onSearch={(e) => searchItems(e, q, setQ, client, setItems, setError)}
      />
      {error && <div className="text-red-600">{error}</div>}
      <ul className="space-y-2">
        {items.map((i) => renderItem(i, client, refresh, setError))}
      </ul>
    </div>
  );
}

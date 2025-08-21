import { TextEncoder, TextDecoder } from 'util';
import { ReadableStream } from 'stream/web';
(global as any).TextEncoder = TextEncoder;
(global as any).TextDecoder = TextDecoder;
(global as any).ReadableStream = ReadableStream;
import { renderHook } from '@testing-library/react';
import { useAgentRunner } from '../../../hooks/useAgentRunner.ts';

describe('useAgentRunner', () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost';
  });

  function stream(chunks: string[], status = 200) {
    const rs = new ReadableStream({
      start(c) {
        chunks.forEach((t) => c.enqueue(new TextEncoder().encode(t)));
        c.close();
      },
    });
    return { body: rs, status, ok: status >= 200 && status < 300 } as any;
  }

  it('streams responses', async () => {
    global.fetch = async () => stream(['hi']);
    const { result } = renderHook(() => useAgentRunner());
    const chunks: string[] = [];
    const final = await result.current.run('hey', { onChunk: (c) => chunks.push(c) });
    expect(final).toBe('hi');
    expect(chunks).toEqual(['hi']);
  });

  it('retries on failure', async () => {
    let calls = 0;
    global.fetch = async () => {
      calls += 1;
      return calls === 1 ? stream([], 500) : stream(['ok']);
    };
    const { result } = renderHook(() => useAgentRunner());
    const final = await result.current.run('a');
    expect(final).toBe('ok');
    expect(calls).toBe(2);
  });

  it('throws after exhausting retries', async () => {
    global.fetch = async () => stream([], 500);
    const { result } = renderHook(() => useAgentRunner());
    await expect(result.current.run('fail', { retries: 2 })).rejects.toThrow('HTTP 500');
  });

  it('handles timeout', async () => {
    global.fetch = () => Promise.reject(new DOMException('aborted', 'AbortError'));
    const { result } = renderHook(() => useAgentRunner());
    await expect(result.current.run('hi', { retries: 1 })).rejects.toThrow('aborted');
  });

  it('validates input', async () => {
    const { result } = renderHook(() => useAgentRunner());
    await expect(result.current.run('')).rejects.toThrow();
  });
});

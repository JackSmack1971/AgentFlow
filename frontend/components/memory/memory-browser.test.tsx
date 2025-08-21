import { render, waitFor, act } from '@testing-library/react';
import MemoryBrowser from './memory-browser.tsx';

const mockList = jest.fn();

jest.mock('../../lib/api.ts', () =>
  jest.fn().mockImplementation(() => ({
    listMemoryItems: mockList,
    searchMemoryItems: jest.fn(),
    updateMemoryItem: jest.fn(),
    deleteMemoryItem: jest.fn(),
  })),
);

class MockEventSource {
  static instances: MockEventSource[] = [];
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  constructor(url: string) {
    MockEventSource.instances.push(this);
  }
  close(): void {}
}
(global as any).EventSource = MockEventSource;

beforeEach(() => {
  mockList.mockReset();
  mockList.mockResolvedValue([]);
  MockEventSource.instances = [];
});

test('refreshes on stream events', async () => {
  await act(async () => {
    render(<MemoryBrowser />);
  });
  await waitFor(() => expect(mockList).toHaveBeenCalled());
  const calls = mockList.mock.calls.length;
  act(() => {
    MockEventSource.instances[0].onmessage?.(
      new MessageEvent('message', { data: '{}' }),
    );
  });
  await waitFor(() => expect(mockList.mock.calls.length).toBe(calls + 1));
});

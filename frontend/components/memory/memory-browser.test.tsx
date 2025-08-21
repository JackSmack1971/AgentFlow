import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MemoryBrowser from './memory-browser.tsx';

const mockList = jest.fn();
const mockSearch = jest.fn();
const mockDelete = jest.fn();

jest.mock('../../lib/api.ts', () =>
  jest.fn().mockImplementation(() => ({
    listMemoryItems: mockList,
    searchMemoryItems: mockSearch,
    updateMemoryItem: jest.fn(),
    deleteMemoryItem: mockDelete,
  })),
);

beforeEach(() => {
  mockList.mockReset();
  mockSearch.mockReset();
  mockDelete.mockReset();
  mockList.mockResolvedValue([]);
  mockSearch.mockResolvedValue([]);
});

test('renders and searches memory items', async () => {
  mockList.mockResolvedValueOnce([{ id: '1', text: 'a' }]);
  render(<MemoryBrowser />);
  expect(await screen.findByText('a')).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Search'), { target: { value: 'b' } });
  fireEvent.submit(screen.getByLabelText('Search').closest('form')!);
  await waitFor(() => expect(mockSearch).toHaveBeenCalledWith({ q: 'b' }));
});

test('deletes an item', async () => {
  mockList.mockResolvedValueOnce([{ id: '1', text: 'x' }]);
  render(<MemoryBrowser />);
  expect(await screen.findByText('x')).toBeInTheDocument();
  fireEvent.click(screen.getByText('Delete'));
  await waitFor(() => expect(mockDelete).toHaveBeenCalled());
});

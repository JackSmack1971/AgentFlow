import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AgentForm from '../../../app/(dashboard)/agents/[id]/edit/form.tsx';

const mockUpdate = jest.fn();
jest.mock('../../../lib/api.ts', () => ({
  __esModule: true,
  default: jest.fn(() => ({ updateAgent: mockUpdate })),
}));

const agent = { id: '1', name: 'Agent One' };

describe('AgentForm', () => {
  beforeEach(() => {
    mockUpdate.mockReset();
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost';
  });

  it('submits updates via keyboard', async () => {
    mockUpdate.mockResolvedValue({ id: '1', name: 'New' });
    render(<AgentForm agent={agent} />);
    const input = screen.getByLabelText('Name');
    await userEvent.clear(input);
    await userEvent.type(input, 'New');
    await userEvent.tab();
    const button = screen.getByRole('button', { name: /save/i });
    expect(button).toHaveFocus();
    await userEvent.keyboard('{Enter}');
    expect(mockUpdate).toHaveBeenCalledWith('1', { name: 'New' }, { timeoutMs: 5000, retries: 3 });
  });

  it('shows error state when update fails', async () => {
    mockUpdate.mockRejectedValue(new Error('fail'));
    render(<AgentForm agent={agent} />);
    await userEvent.click(screen.getByRole('button', { name: /save/i }));
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('fail');
  });

  it('has accessible fields', () => {
    mockUpdate.mockResolvedValue(agent);
    render(<AgentForm agent={agent} />);
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
  });
});

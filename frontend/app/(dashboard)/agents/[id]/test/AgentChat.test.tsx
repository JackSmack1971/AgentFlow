import { render, screen, fireEvent } from '@testing-library/react';
import AgentChat from './AgentChat.tsx';

jest.mock('../../../../../hooks/useAgentRunner.ts', () => ({
  useAgentRunner: () => ({
    run: jest.fn(async (_: string, onChunk: (c: string) => void) => {
      onChunk('hi');
      return 'hi';
    }),
  }),
}));

describe('AgentChat', () => {
  it('validates empty input', async () => {
    render(<AgentChat />);
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    expect(screen.queryByText('hi')).toBeNull();
  });

  it('renders messages', async () => {
    render(<AgentChat />);
    const input = screen.getByLabelText('Message');
    fireEvent.change(input, { target: { value: 'hello' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    expect(await screen.findByText('hello')).toBeInTheDocument();
    expect(await screen.findByText('hi')).toBeInTheDocument();
  });
});

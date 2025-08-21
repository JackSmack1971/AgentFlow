import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AgentRunPage from './page.tsx';

process.env.NEXT_PUBLIC_API_URL = 'http://localhost';

describe('AgentRunPage', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('submits prompt and posts data', async () => {
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ result: 'ok' }),
    } as Response);
    (global as any).fetch = fetchMock;
    render(<AgentRunPage />);
    fireEvent.change(screen.getByLabelText(/prompt/i), { target: { value: 'hi' } });
    fireEvent.click(screen.getByRole('button', { name: /run/i }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost/agents/run',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'hi' }),
        signal: expect.any(AbortSignal),
      }),
    ));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('shows validation error for empty prompt', async () => {
    const fetchMock = jest.fn();
    (global as any).fetch = fetchMock;
    render(<AgentRunPage />);
    fireEvent.click(screen.getByRole('button', { name: /run/i }));
    await waitFor(() => expect(screen.getByText('Prompt is required')).toBeInTheDocument());
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('shows error message on request failure', async () => {
    const fetchMock = jest.fn().mockRejectedValue(new Error('bad'));
    (global as any).fetch = fetchMock;
    render(<AgentRunPage />);
    fireEvent.change(screen.getByLabelText(/prompt/i), { target: { value: 'fail' } });
    fireEvent.click(screen.getByRole('button', { name: /run/i }));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('bad'));
  });
});


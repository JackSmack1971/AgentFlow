import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginPage from './page.tsx';
import { useAuth } from '../../../providers/auth-provider.ts';
import { useRouter } from 'next/navigation';

jest.mock('../../../providers/auth-provider.ts', () => ({
  useAuth: jest.fn(),
}));

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

describe('LoginPage', () => {
  const push = jest.fn();

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({ push });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('submits valid credentials and redirects', async () => {
    const login = jest.fn().mockResolvedValue(undefined);
    (useAuth as jest.Mock).mockReturnValue({ login, loading: false });
    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText(/password/i), {
      target: { value: 'secret' },
    });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => expect(login).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'secret',
    }));
    expect(push).toHaveBeenCalledWith('/dashboard');
  });

  it('shows validation errors for invalid inputs', async () => {
    const login = jest.fn();
    (useAuth as jest.Mock).mockReturnValue({ login, loading: false });
    render(<LoginPage />);

    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByText('Invalid email')).toBeInTheDocument();
      expect(
        screen.getByText('String must contain at least 1 character(s)')
      ).toBeInTheDocument();
    });
    expect(login).not.toHaveBeenCalled();
    expect(push).not.toHaveBeenCalled();
  });

  it('disables button when loading', () => {
    const login = jest.fn();
    (useAuth as jest.Mock).mockReturnValue({ login, loading: true });
    render(<LoginPage />);

    const button = screen.getByRole('button', { name: /loading/i });
    expect(button).toBeDisabled();
  });

  it('shows error message on login failure', async () => {
    const login = jest.fn().mockRejectedValue(new Error('bad'));
    (useAuth as jest.Mock).mockReturnValue({ login, loading: false });
    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText(/password/i), {
      target: { value: 'secret' },
    });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => expect(screen.getByText('bad')).toBeInTheDocument());
    expect(push).not.toHaveBeenCalled();
  });
});

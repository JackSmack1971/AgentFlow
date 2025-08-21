import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import RegisterPage from './page.tsx';
import { useRouter } from 'next/navigation';
import * as utils from './utils.ts';

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

jest.mock('../../../lib/api.ts', () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({ request: jest.fn() })),
}));

jest.mock('./utils.ts', () => {
  const actual = jest.requireActual('./utils.ts');
  return { ...actual, registerUser: jest.fn() };
});

describe('RegisterPage', () => {
  const push = jest.fn();

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({ push });
  });

  afterEach(() => {
    jest.clearAllMocks();
    jest.useRealTimers();
  });

  it('submits valid data and redirects to login', async () => {
    jest.useFakeTimers();
    (utils.registerUser as jest.Mock).mockResolvedValue(undefined);
    render(<RegisterPage />);

    fireEvent.change(screen.getByPlaceholderText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'password123' },
    });
    fireEvent.change(screen.getByPlaceholderText('Confirm Password'), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => expect(utils.registerUser).toHaveBeenCalled());
    expect(screen.getByText('Registration successful')).toBeInTheDocument();

    act(() => {
      jest.runAllTimers();
    });
    expect(push).toHaveBeenCalledWith('/login');
  });

  it('shows validation errors for mismatched passwords', async () => {
    render(<RegisterPage />);

    fireEvent.change(screen.getByPlaceholderText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'password123' },
    });
    fireEvent.change(screen.getByPlaceholderText('Confirm Password'), {
      target: { value: 'different' },
    });
    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() =>
      expect(screen.getByText('Passwords must match')).toBeInTheDocument()
    );
    expect(utils.registerUser).not.toHaveBeenCalled();
  });

  it('disables button and shows loading state', async () => {
    let resolveFn: () => void;
    (utils.registerUser as jest.Mock).mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          resolveFn = resolve;
        }),
    );
    render(<RegisterPage />);

    fireEvent.change(screen.getByPlaceholderText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'password123' },
    });
    fireEvent.change(screen.getByPlaceholderText('Confirm Password'), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      const button = screen.getByRole('button', { name: /loading/i });
      expect(button).toBeDisabled();
    });

    act(() => resolveFn());
  });

  it('shows error message on failure', async () => {
    (utils.registerUser as jest.Mock).mockRejectedValue(
      new utils.RegisterError('failed'),
    );
    render(<RegisterPage />);

    fireEvent.change(screen.getByPlaceholderText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'password123' },
    });
    fireEvent.change(screen.getByPlaceholderText('Confirm Password'), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => expect(screen.getByText('failed')).toBeInTheDocument());
    expect(push).not.toHaveBeenCalled();
  });
});

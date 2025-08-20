import { z } from 'zod';

export const registerSchema = z
  .object({
    email: z.string().email(),
    password: z.string().min(8),
    confirmPassword: z.string().min(8),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: 'Passwords must match',
    path: ['confirmPassword'],
  });

export type RegisterValues = z.infer<typeof registerSchema>;

export class RegisterError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'RegisterError';
  }
}

type Client = {
  request: (
    endpoint: string,
    init?: RequestInit & { timeoutMs?: number; retries?: number },
  ) => Promise<unknown>;
};

export async function registerUser(
  values: RegisterValues,
  client: Client,
): Promise<void> {
  const data = registerSchema.parse(values);
  try {
    await client.request('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: data.email, password: data.password }),
      timeoutMs: 5000,
      retries: 3,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Registration failed';
    throw new RegisterError(message);
  }
}

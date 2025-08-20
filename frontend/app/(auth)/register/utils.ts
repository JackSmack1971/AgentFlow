import ApiClient from '../../../lib/api.ts';
import { z } from 'zod';

export class RegistrationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'RegistrationError';
  }
}

export const registerSchema = z
  .object({
    email: z.string().email(),
    password: z.string().min(8),
    confirmPassword: z.string().min(8),
  })
  .superRefine((data, ctx) => {
    if (data.password !== data.confirmPassword) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['confirmPassword'],
        message: 'Passwords do not match',
      });
    }
  });

export type RegisterValues = z.infer<typeof registerSchema>;

export async function registerUser(
  client: ApiClient,
  values: RegisterValues,
): Promise<void> {
  const data = registerSchema.parse(values);
  try {
    await (client as any).request('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: data.email, password: data.password }),
      timeoutMs: 5000,
      retries: 3,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Registration failed';
    throw new RegistrationError(message);
  }
}

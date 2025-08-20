import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export type LoginValues = z.infer<typeof loginSchema>;

export async function handleLogin(
  values: LoginValues,
  loginFn: (v: LoginValues) => Promise<void>,
  push: (path: string) => void,
): Promise<string | null> {
  try {
    await loginFn(values);
    push('/dashboard');
    return null;
  } catch (err) {
    return err instanceof Error ? err.message : 'Login failed';
  }
}

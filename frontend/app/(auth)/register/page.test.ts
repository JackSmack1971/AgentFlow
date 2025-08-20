import assert from 'node:assert/strict';
import { registerSchema, registerUser, type RegisterValues, RegisterError } from './utils.ts';

async function run(): Promise<void> {
  assert.throws(() => registerSchema.parse({ email: 'x', password: 'a', confirmPassword: 'b' }));
  const ok: RegisterValues = { email: 'a@b.com', password: 'password', confirmPassword: 'password' };
  const goodClient = { request: async () => ({}) } as any;
  await registerUser(ok, goodClient);
  const badClient = { request: async () => { throw new Error('fail'); } } as any;
  await assert.rejects(() => registerUser(ok, badClient), RegisterError);
}

run().then(() => console.log('Register page tests passed'));

import assert from 'node:assert/strict';
import { registerSchema, registerUser, type RegisterValues, RegistrationError } from './utils.ts';

async function run() {
  assert.throws(() => registerSchema.parse({ email: 'bad', password: '12345678', confirmPassword: '12345678' }));
  assert.throws(
    () => registerSchema.parse({ email: 'a@b.com', password: '12345678', confirmPassword: '87654321' }),
    /Passwords do not match/,
  );
  const ok: RegisterValues = { email: 'a@b.com', password: '12345678', confirmPassword: '12345678' };
  const clientOk = { request: async () => ({}) } as any;
  await registerUser(clientOk, ok);
  const clientFail = { request: async () => { throw new Error('fail'); } } as any;
  await assert.rejects(() => registerUser(clientFail, ok), RegistrationError);
}

run().then(() => console.log('Register page tests passed'));

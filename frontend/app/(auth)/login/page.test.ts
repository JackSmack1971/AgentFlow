import assert from 'node:assert/strict';
import { loginSchema, handleLogin, type LoginValues } from './utils.ts';

async function run() {
  assert.throws(() => loginSchema.parse({ email: 'no', password: '' }));
  let pushed = '';
  const ok: LoginValues = { email: 'a@b.com', password: 'x' };
  const msg = await handleLogin(ok, async () => {}, (p) => { pushed = p; });
  assert.equal(msg, null);
  assert.equal(pushed, '/dashboard');
  let pushed2 = '';
  const msg2 = await handleLogin(
    ok,
    async () => {
      throw new Error('bad');
    },
    (p) => {
      pushed2 = p;
    },
  );
  assert.equal(msg2, 'bad');
  assert.equal(pushed2, '');
}

run().then(() => console.log('Login page tests passed'));

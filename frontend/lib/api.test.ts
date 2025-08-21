import assert from 'node:assert/strict';
import ApiClient from './api.ts';

function resetEnv() {
  delete process.env.NEXT_PUBLIC_API_BASE_URL;
}

function testInstantiation() {
  resetEnv();
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
  const client = new ApiClient();
  assert.ok(client);
}

function testMissingBaseUrl() {
  resetEnv();
  assert.throws(() => new ApiClient(), /API base URL not configured/);
}

async function testListAgents() {
  resetEnv();
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost';
  (global as any).fetch = async () =>
    new Response(
      JSON.stringify([{ id: '1', name: 'A1' }]),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    );
  const client = new ApiClient();
  const agents = await client.listAgents();
  assert.equal(agents[0].name, 'A1');
}

testInstantiation();
testMissingBaseUrl();
(async () => {
  await testListAgents();
  console.log('All tests passed');
})();

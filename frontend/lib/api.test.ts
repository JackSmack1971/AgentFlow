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

testInstantiation();
testMissingBaseUrl();

console.log('All tests passed');

const nextJest = require('next/jest');

const createJestConfig = nextJest({ dir: './' });

/** @type {import('jest').Config} */
const customJestConfig = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  testMatch: [
    '<rootDir>/app/(auth)/login/page.test.tsx',
    '<rootDir>/app/(auth)/register/page.test.tsx',
    '<rootDir>/app/(dashboard)/agents/create/page.test.tsx',
  ],
};

module.exports = createJestConfig(customJestConfig);

/**
 * Test Setup Configuration
 * Global setup for Jest tests with comprehensive utilities
 */

import { jest } from '@jest/globals';

// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.RABBITMQ_HOST = 'localhost';
process.env.RABBITMQ_PORT = '5672';
process.env.RABBITMQ_USER = 'test_user';
process.env.RABBITMQ_PASS = 'test_pass';
process.env.RABBITMQ_URL = 'amqp://localhost:5672';
process.env.ORCHESTRATOR_QUEUE = 'test_orchestrator';
process.env.TASK_EXCHANGE = 'test_tasks';
process.env.RESULT_EXCHANGE = 'test_results';
process.env.AGENT_ID = 'test-agent-001';
process.env.AGENT_NAME = 'Test Agent';
process.env.HEARTBEAT_INTERVAL = '30';
process.env.AUTO_RECONNECT = 'false';
process.env.PREFETCH_COUNT = '1';

// Global test utilities
global.testUtils = {
  // Wait for async operations
  wait: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

  // Create test timeout
  timeout: (ms = 5000) => new Promise((_, reject) =>
    setTimeout(() => reject(new Error('Test timeout')), ms)
  ),

  // Mock console methods to reduce noise
  silenceConsole: () => {
    global.originalConsole = {
      log: console.log,
      error: console.error,
      warn: console.warn,
      info: console.info
    };
    console.log = jest.fn();
    console.error = jest.fn();
    console.warn = jest.fn();
    console.info = jest.fn();
  },

  // Restore console methods
  restoreConsole: () => {
    if (global.originalConsole) {
      console.log = global.originalConsole.log;
      console.error = global.originalConsole.error;
      console.warn = global.originalConsole.warn;
      console.info = global.originalConsole.info;
    }
  }
};

// Suppress console logs during tests (optional)
if (process.env.SUPPRESS_LOGS === 'true') {
  global.testUtils.silenceConsole();
}

// Global test timeout
jest.setTimeout(30000);

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});

// Clean up after all tests
afterAll(async () => {
  global.testUtils.restoreConsole();
  // Close any open connections
  await new Promise(resolve => setTimeout(resolve, 100));
});

// Global error handler
process.on('unhandledRejection', (error) => {
  console.error('Unhandled Promise Rejection in tests:', error);
});

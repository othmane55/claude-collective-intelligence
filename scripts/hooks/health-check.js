#!/usr/bin/env node
/**
 * Health Check Hook
 * Periodic health check and heartbeat
 */

import { RabbitMQClient } from '../rabbitmq-client.js';
import dotenv from 'dotenv';

dotenv.config();

async function healthCheck() {
  try {
    const client = new RabbitMQClient();
    await client.connect();

    // Publish heartbeat
    await client.publishStatus({
      event: 'heartbeat',
      healthy: true,
      timestamp: Date.now()
    }, 'agent.status.heartbeat');

    console.log('💓 Heartbeat sent');

    await client.close();
    process.exit(0);
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
    process.exit(1);
  }
}

healthCheck();

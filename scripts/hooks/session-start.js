#!/usr/bin/env node
/**
 * Session Start Hook
 * Initializes RabbitMQ connection when Claude Code session starts
 */

import { RabbitMQClient } from '../rabbitmq-client.js';
import dotenv from 'dotenv';

dotenv.config();

async function main() {
  try {
    console.log('🚀 Session Start Hook: Initializing RabbitMQ connection...');

    const client = new RabbitMQClient();
    await client.connect();

    // Verify connection
    if (client.isHealthy()) {
      console.log('✅ RabbitMQ connection established');
      console.log(`   Agent ID: ${client.agentId}`);
      console.log(`   RabbitMQ URL: ${process.env.RABBITMQ_URL || 'amqp://localhost:5672'}`);
    } else {
      console.warn('⚠️  RabbitMQ connection unhealthy');
      process.exit(1);
    }

    // Close connection (will be reopened by orchestrator)
    await client.close();

    process.exit(0);
  } catch (error) {
    console.error('❌ Session start hook failed:', error.message);
    console.error('   Make sure RabbitMQ is running:');
    console.error('   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management');
    process.exit(1);
  }
}

main();

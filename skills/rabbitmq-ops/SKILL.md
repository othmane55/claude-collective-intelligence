---
name: rabbitmq-operations
description: Manage RabbitMQ connections, queues, exchanges, and message routing. Use when working with message queues, pub/sub patterns, or distributed messaging.
---

# RabbitMQ Operations

Comprehensive skill for managing RabbitMQ in multi-agent orchestration systems.

## Quick Start

### Basic Connection
```javascript
import { RabbitMQClient } from './scripts/rabbitmq-client.js';

const client = new RabbitMQClient({
  url: 'amqp://localhost:5672'
});

await client.connect();
```

### Send Message to Queue
```javascript
await client.publishTask({
  title: "Process data",
  description: "Transform CSV to JSON",
  priority: "high"
});
```

### Consume Messages
```javascript
await client.consumeTasks('agent.tasks', async (msg, { ack, nack }) => {
  console.log('Received:', msg.task);

  // Process task
  const result = await processTask(msg.task);

  // Acknowledge
  ack();
});
```

## Core Concepts

### Queues
Point-to-point messaging with load balancing:

```javascript
// Setup durable queue
await client.setupTaskQueue('agent.tasks');

// Multiple consumers share work
// Each message delivered to ONE consumer
```

### Exchanges
Publish-subscribe with routing:

```javascript
// Fanout - broadcast to all
await client.setupBrainstormExchange('agent.brainstorm');

// Topic - selective routing
await client.setupStatusExchange('agent.status');
```

### Message Patterns

**Work Queue** (Load Balancing):
```
Producer → Queue → Consumer 1
                 → Consumer 2
                 → Consumer 3

Each message to ONE consumer
```

**Pub/Sub** (Broadcasting):
```
Publisher → Exchange → Queue 1 → Consumer 1
                    → Queue 2 → Consumer 2
                    → Queue 3 → Consumer 3

Each message to ALL consumers
```

**Topic** (Selective):
```
Publisher → Topic Exchange
   ↓ (routing key: agent.status.connected)
   → Queue (pattern: agent.status.#) → Consumer 1
   → Queue (pattern: agent.*.connected) → Consumer 2
```

## Advanced Operations

### Message Persistence
```javascript
// Durable queue + persistent messages = survive restarts
await channel.assertQueue('agent.tasks', {
  durable: true  // Queue survives broker restart
});

await channel.sendToQueue('agent.tasks', message, {
  persistent: true  // Message written to disk
});
```

### Prefetch (QoS)
```javascript
// Fair dispatch - each worker gets 1 task at a time
await channel.prefetch(1);

// Or allow multiple concurrent tasks per worker
await channel.prefetch(5);
```

### Message TTL
```javascript
// Messages expire after 1 hour
await channel.assertQueue('agent.tasks', {
  arguments: {
    'x-message-ttl': 3600000
  }
});
```

### Dead Letter Exchange
```javascript
// Failed messages go to dead letter queue
await channel.assertQueue('agent.tasks', {
  arguments: {
    'x-dead-letter-exchange': 'dlx',
    'x-dead-letter-routing-key': 'failed'
  }
});
```

### Priority Queues
```javascript
await channel.assertQueue('agent.tasks', {
  arguments: {
    'x-max-priority': 10
  }
});

// Send with priority
await channel.sendToQueue('agent.tasks', message, {
  priority: 8
});
```

## Connection Management

### Auto-Reconnect
```javascript
const client = new RabbitMQClient({
  autoReconnect: true,
  maxReconnectAttempts: 10
});

client.on('disconnected', () => {
  console.log('Connection lost, will retry...');
});

client.on('connected', () => {
  console.log('Reconnected successfully!');
});
```

### Heartbeat
```javascript
// Keep connection alive
const client = new RabbitMQClient({
  heartbeat: 30  // Send heartbeat every 30s
});
```

### Connection Pooling
```javascript
// For high-throughput scenarios
const pool = new ConnectionPool({
  min: 2,
  max: 10,
  url: 'amqp://localhost:5672'
});

const channel = await pool.acquire();
// Use channel
await pool.release(channel);
```

## Message Acknowledgment

### Manual Ack
```javascript
await client.consumeTasks('queue', async (msg, { ack, nack, reject }) => {
  try {
    await processMessage(msg);
    ack();  // Success
  } catch (error) {
    if (error.isTransient) {
      nack(true);  // Requeue for retry
    } else {
      reject();  // Dead letter
    }
  }
}, { noAck: false });
```

### Auto-Ack (Risky)
```javascript
// Message lost if processing fails!
await channel.consume('queue', handler, { noAck: true });
```

## Routing Patterns

### Direct Exchange
```javascript
await channel.assertExchange('direct_logs', 'direct');

// Bind with routing key
await channel.bindQueue(queue, 'direct_logs', 'error');
await channel.bindQueue(queue, 'direct_logs', 'warning');

// Publish with routing key
await channel.publish('direct_logs', 'error', message);
```

### Topic Exchange
```javascript
await channel.assertExchange('logs', 'topic');

// Wildcards in binding:
// * matches one word
// # matches zero or more words

await channel.bindQueue(queue, 'logs', 'agent.status.*');
await channel.bindQueue(queue, 'logs', 'agent.#');

// Publish
await channel.publish('logs', 'agent.status.connected', message);
```

### Fanout Exchange
```javascript
await channel.assertExchange('notifications', 'fanout');

// All bound queues receive message
await channel.bindQueue(queue1, 'notifications', '');
await channel.bindQueue(queue2, 'notifications', '');

await channel.publish('notifications', '', message);
// Both queue1 and queue2 receive it
```

## Monitoring and Debugging

### Queue Inspection
```javascript
// Check queue status
const info = await channel.checkQueue('agent.tasks');
console.log('Messages:', info.messageCount);
console.log('Consumers:', info.consumerCount);
```

### Management API
```javascript
// Use RabbitMQ Management HTTP API
const response = await fetch('http://localhost:15672/api/queues', {
  headers: {
    'Authorization': 'Basic ' + btoa('guest:guest')
  }
});

const queues = await response.json();
queues.forEach(q => {
  console.log(`${q.name}: ${q.messages} messages`);
});
```

### Consumer Tracking
```javascript
const consumer = await channel.consume('queue', handler);

// Cancel consumer
await channel.cancel(consumer.consumerTag);
```

## Performance Optimization

### Batch Publishing
```javascript
// Publish multiple messages efficiently
const messages = [...];

for (const msg of messages) {
  channel.sendToQueue('queue', Buffer.from(JSON.stringify(msg)));
}

// Wait for all to be written
await channel.waitForConfirms();
```

### Publisher Confirms
```javascript
await channel.confirmSelect();

channel.sendToQueue('queue', message);

await channel.waitForConfirms();
// Message definitely received by broker
```

### Consumer Concurrency
```javascript
// Multiple channels for parallel processing
const channels = await Promise.all([
  connection.createChannel(),
  connection.createChannel(),
  connection.createChannel()
]);

channels.forEach((ch, i) => {
  ch.consume('queue', handler);
});
```

## Error Handling

### Channel Errors
```javascript
channel.on('error', (err) => {
  console.error('Channel error:', err);
  // Channel is closed, create new one
});

channel.on('close', () => {
  console.log('Channel closed');
});
```

### Connection Errors
```javascript
connection.on('error', (err) => {
  console.error('Connection error:', err);
});

connection.on('close', () => {
  console.log('Connection closed');
  // Implement reconnection logic
});
```

### Message Handling Errors
```javascript
try {
  await processMessage(msg);
  ack();
} catch (error) {
  console.error('Processing error:', error);

  // Log error with context
  await logError({
    messageId: msg.properties.messageId,
    error: error.message,
    stack: error.stack,
    timestamp: Date.now()
  });

  // Decide: retry or dead letter
  if (shouldRetry(error)) {
    nack(true);  // Requeue
  } else {
    reject();  // Dead letter
  }
}
```

## Best Practices

1. **Use Persistent Messages for Critical Data**
   ```javascript
   sendToQueue(queue, msg, { persistent: true });
   ```

2. **Set Reasonable Prefetch**
   ```javascript
   await channel.prefetch(1);  // Fair dispatch
   ```

3. **Always Close Connections**
   ```javascript
   process.on('SIGINT', async () => {
     await channel.close();
     await connection.close();
   });
   ```

4. **Use Confirm Channels for Reliability**
   ```javascript
   await channel.confirmSelect();
   await channel.waitForConfirms();
   ```

5. **Monitor Queue Depths**
   ```javascript
   setInterval(async () => {
     const info = await channel.checkQueue('queue');
     if (info.messageCount > 100) {
       alert('High queue depth!');
     }
   }, 60000);
   ```

6. **Implement Dead Letter Queues**
   ```javascript
   // Capture and analyze failed messages
   ```

7. **Use Message TTL**
   ```javascript
   // Prevent old messages from clogging queues
   ```

8. **Set Max Length**
   ```javascript
   await channel.assertQueue('queue', {
     arguments: { 'x-max-length': 10000 }
   });
   ```

## Common Patterns

### Request-Reply
```javascript
// Request
const correlationId = uuid();
const replyQueue = await channel.assertQueue('', { exclusive: true });

await channel.sendToQueue('rpc_queue', msg, {
  correlationId,
  replyTo: replyQueue.queue
});

// Wait for reply
await channel.consume(replyQueue.queue, (reply) => {
  if (reply.properties.correlationId === correlationId) {
    // Process reply
  }
});
```

### Work Stealing
```javascript
// Workers can steal work from each other
await channel.prefetch(1);
await channel.consume('queue', async (msg) => {
  // Process
  ack();
});
```

### Circuit Breaker
```javascript
let failureCount = 0;
const threshold = 5;

await channel.consume('queue', async (msg) => {
  try {
    await process(msg);
    failureCount = 0;
    ack();
  } catch (error) {
    failureCount++;

    if (failureCount >= threshold) {
      console.error('Circuit open, stopping consumption');
      await channel.cancel(consumerTag);
    } else {
      nack(true);
    }
  }
});
```

## Resources

- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [amqplib Documentation](https://amqp-node.github.io/amqplib/)
- [RabbitMQ Tutorials](https://www.rabbitmq.com/getstarted.html)
- Plugin scripts: `scripts/rabbitmq-client.js`

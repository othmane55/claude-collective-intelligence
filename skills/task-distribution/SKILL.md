---
name: task-distribution
description: Distribute work across multiple agents using queue-based load balancing. Use for parallel execution, work distribution, and team coordination.
---

# Task Distribution

Efficiently distribute work across multiple Claude Code agents using RabbitMQ queues.

## Quick Start

### Distribute Task (Team Leader)
```javascript
import AgentOrchestrator from './scripts/orchestrator.js';

const orchestrator = new AgentOrchestrator('team-leader');
await orchestrator.initialize();
await orchestrator.startTeamLeader();

// Assign task to worker pool
await orchestrator.assignTask({
  title: "Implement authentication",
  description: "JWT-based auth with refresh tokens",
  priority: "high"
});
```

### Receive and Execute Task (Worker)
```javascript
const orchestrator = new AgentOrchestrator('worker');
await orchestrator.initialize();
await orchestrator.startWorker();

// Automatically consumes and processes tasks
```

## Distribution Strategies

### Strategy 1: Round-Robin (Fair Distribution)
```javascript
// RabbitMQ default behavior with prefetch=1
await channel.prefetch(1);

// Tasks distributed evenly:
// Task 1 → Worker A
// Task 2 → Worker B
// Task 3 → Worker C
// Task 4 → Worker A
// ...
```

### Strategy 2: Priority-Based
```javascript
// High priority tasks processed first
await orchestrator.assignTask({
  title: "Critical bug fix",
  priority: "critical"  // Processed before normal/low
});

await orchestrator.assignTask({
  title: "Refactoring",
  priority: "low"  // Processed last
});
```

### Strategy 3: Capability-Based Routing
```javascript
// Route to specialized workers
const task = {
  title: "Optimize database queries",
  requiredCapability: "database"
};

// Only database specialists pick this up
```

### Strategy 4: Batch Distribution
```javascript
// Distribute multiple related tasks
const tasks = [
  { title: "Process file 1.csv" },
  { title: "Process file 2.csv" },
  { title: "Process file 3.csv" }
];

for (const task of tasks) {
  await orchestrator.assignTask(task);
}

// Workers process in parallel
```

## Load Balancing

### Fair Queue Behavior
```javascript
// Each worker gets equal share
// No worker idle while tasks pending
// Automatic rebalancing on worker join/leave

// 100 tasks, 5 workers
// Each worker processes ~20 tasks
```

### Prefetch Control
```javascript
// Conservative (fair, slower)
await channel.prefetch(1);
// Each worker gets 1 task at a time

// Aggressive (less fair, faster)
await channel.prefetch(5);
// Each worker can have 5 tasks in flight

// Dynamic
const prefetch = Math.ceil(availableCPU / workerCount);
await channel.prefetch(prefetch);
```

### Worker Scaling
```javascript
// Detect queue buildup
const queueDepth = await getQueueDepth('agent.tasks');
const workerCount = await getConnectedWorkers();

if (queueDepth / workerCount > 10) {
  console.log('⚠️ Queue backing up, start more workers!');
  // Recommendation: scale horizontally
}
```

## Task Lifecycle Management

### Task States
```javascript
const taskStates = {
  PENDING: 'queued',      // In queue, not yet picked up
  ACTIVE: 'processing',   // Worker is executing
  COMPLETED: 'done',      // Successfully finished
  FAILED: 'error'         // Execution failed
};
```

### State Tracking
```javascript
// Team leader tracks all tasks
const taskTracker = new Map();

// On assign
taskTracker.set(taskId, {
  state: 'PENDING',
  assignedAt: Date.now()
});

// On worker pickup (via status message)
taskTracker.set(taskId, {
  state: 'ACTIVE',
  workerId: 'worker-01',
  startedAt: Date.now()
});

// On completion
taskTracker.set(taskId, {
  state: 'COMPLETED',
  result: {...},
  completedAt: Date.now(),
  duration: completedAt - startedAt
});
```

### Progress Monitoring
```javascript
// Worker reports progress
await publishStatus({
  event: 'task_progress',
  taskId,
  progress: 0.5,  // 50% complete
  message: 'Halfway through data processing'
}, 'agent.status.task.progress');

// Team leader receives and displays
console.log(`Task ${taskId}: 50% complete`);
```

## Retry and Failure Handling

### Automatic Retry
```javascript
// Worker handles task with retry logic
await client.consumeTasks('agent.tasks', async (msg, { ack, nack, reject }) => {
  const { task } = msg;

  try {
    await executeTask(task);
    ack();  // Success
  } catch (error) {
    // Retry if transient error
    if (task.retryCount > 0) {
      console.log(`Retrying (${task.retryCount} attempts left)`);

      task.retryCount--;
      nack(true);  // Requeue for another worker
    } else {
      console.error('Max retries reached');
      reject();  // Send to dead letter
    }
  }
});
```

### Dead Letter Queue
```javascript
// Configure DLQ for failed tasks
await channel.assertQueue('agent.tasks', {
  arguments: {
    'x-dead-letter-exchange': 'dlx.tasks',
    'x-dead-letter-routing-key': 'failed'
  }
});

// Analyze failed tasks
await channel.consume('dlq.tasks', async (msg) => {
  console.error('Task failed permanently:', msg);

  // Notify team leader
  await publishStatus({
    event: 'task_dead_letter',
    task: msg.task,
    reason: msg.properties.headers['x-death']
  }, 'agent.status.task.failed');
});
```

### Circuit Breaker
```javascript
// Stop consuming if too many failures
let consecutiveFailures = 0;
const failureThreshold = 5;

await client.consumeTasks('agent.tasks', async (msg, { ack, nack }) => {
  try {
    await executeTask(msg.task);
    consecutiveFailures = 0;  // Reset
    ack();
  } catch (error) {
    consecutiveFailures++;

    if (consecutiveFailures >= failureThreshold) {
      console.error('Circuit breaker opened!');
      await channel.cancel(consumerTag);
      await publishStatus({
        event: 'circuit_breaker_open',
        reason: 'Too many consecutive failures'
      }, 'agent.status.error');
    } else {
      nack(true);
    }
  }
});
```

## Work Distribution Patterns

### Pattern 1: Map-Reduce
```javascript
// Map phase: distribute work
const chunks = splitDataIntoChunks(largeDataset);

for (const chunk of chunks) {
  await assignTask({
    title: `Process chunk ${chunk.id}`,
    data: chunk
  });
}

// Reduce phase: aggregate results
const results = [];
await consumeResults('agent.results', async (msg) => {
  results.push(msg.result);

  if (results.length === chunks.length) {
    const finalResult = reduce(results);
    console.log('Map-reduce complete:', finalResult);
  }
});
```

### Pattern 2: Pipeline
```javascript
// Sequential processing across multiple workers
// Worker A → Queue 1 → Worker B → Queue 2 → Worker C

// Worker A: Fetch data
await publishTask({ title: 'Fetch data' }, 'queue.fetch');

// Worker B: Transform data
await consumeTasks('queue.fetch', async (msg, { ack }) => {
  const data = await fetchData();
  await publishTask({ title: 'Transform', data }, 'queue.transform');
  ack();
});

// Worker C: Load data
await consumeTasks('queue.transform', async (msg, { ack }) => {
  const transformed = await transform(msg.data);
  await loadData(transformed);
  ack();
});
```

### Pattern 3: Fan-Out / Fan-In
```javascript
// One task spawns multiple sub-tasks
await consumeTasks('agent.tasks', async (msg, { ack }) => {
  const { task } = msg;

  if (task.type === 'parallel') {
    // Fan out
    const subtasks = task.subtasks;
    for (const subtask of subtasks) {
      await assignTask(subtask);
    }

    // Track completion
    let completed = 0;
    await consumeResults('agent.results', (result) => {
      completed++;

      if (completed === subtasks.length) {
        // Fan in - all subtasks complete
        console.log('All parallel tasks complete');
      }
    });
  }

  ack();
});
```

## Performance Optimization

### Batch Assignment
```javascript
// Assign multiple tasks efficiently
const tasks = generateTasks(100);

// Don't await each task
const promises = tasks.map(task => assignTask(task));

// Wait for all assignments
await Promise.all(promises);
```

### Prefetching Optimization
```javascript
// Balance fairness vs throughput
const optimalPrefetch = calculatePrefetch({
  avgTaskDuration: 2000,   // 2 seconds
  workerCount: 5,
  targetLatency: 1000      // 1 second max wait
});

await channel.prefetch(optimalPrefetch);
```

### Connection Pooling
```javascript
// Multiple channels for high throughput
const channels = await createChannelPool(5);

// Distribute assignments across channels
let channelIndex = 0;
for (const task of tasks) {
  const channel = channels[channelIndex % channels.length];
  await channel.sendToQueue('agent.tasks', task);
  channelIndex++;
}
```

## Monitoring and Metrics

### Distribution Metrics
```javascript
const metrics = {
  tasksAssigned: 0,
  tasksCompleted: 0,
  tasksFailed: 0,
  avgDuration: 0,
  queueDepth: 0,
  activeWorkers: 0
};

// Track assignment
metrics.tasksAssigned++;

// Track completion
metrics.tasksCompleted++;
metrics.avgDuration = calculateAverage(completionTimes);

// Monitor queue
setInterval(async () => {
  const info = await channel.checkQueue('agent.tasks');
  metrics.queueDepth = info.messageCount;
  metrics.activeWorkers = info.consumerCount;
}, 10000);
```

### Health Checks
```javascript
// Periodic health check
setInterval(async () => {
  const health = {
    queueDepth: await getQueueDepth(),
    workerCount: await getWorkerCount(),
    avgProcessingTime: calculateAvg(),
    failureRate: calculateFailureRate()
  };

  if (health.queueDepth > 100) {
    alert('High queue depth - scale up workers');
  }

  if (health.failureRate > 0.1) {
    alert('High failure rate - investigate workers');
  }
}, 60000);
```

## Best Practices

1. **Use Persistent Messages for Critical Tasks**
   ```javascript
   await channel.sendToQueue('queue', msg, { persistent: true });
   ```

2. **Set Reasonable Retry Limits**
   ```javascript
   task.retryCount = 3;  // Don't retry forever
   ```

3. **Implement Idempotent Task Handlers**
   ```javascript
   // Task can be safely retried
   async function handleTask(task) {
     // Check if already processed
     if (await isProcessed(task.id)) return;
     // Process
     await process(task);
     // Mark processed
     await markProcessed(task.id);
   }
   ```

4. **Monitor Queue Depth**
   ```javascript
   // Alert if queue backing up
   if (queueDepth > threshold) {
     scaleUpWorkers();
   }
   ```

5. **Use Priority for Critical Tasks**
   ```javascript
   // Production bugs first
   task.priority = 'critical';
   ```

6. **Fair Prefetch for Even Distribution**
   ```javascript
   await channel.prefetch(1);  // Fair distribution
   ```

7. **Graceful Shutdown**
   ```javascript
   process.on('SIGTERM', async () => {
     // Finish current task
     await channel.cancel(consumerTag);
     await channel.close();
   });
   ```

## Examples

See `examples/` directory for:
- `map-reduce.js` - Parallel data processing
- `pipeline.js` - Sequential workflow
- `fan-out-fan-in.js` - Parallel sub-tasks
- `priority-queue.js` - Priority-based execution
- `retry-dlq.js` - Retry and dead letter handling

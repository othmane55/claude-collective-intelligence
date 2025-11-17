---
name: health-monitoring
description: Monitor system health, track metrics, detect anomalies, and generate alerts for the multi-agent orchestration system.
---

# Health Monitoring

Comprehensive monitoring and observability for distributed agent systems.

## Quick Start

### Basic Monitoring
```javascript
import AgentOrchestrator from './scripts/orchestrator.js';

const monitor = new AgentOrchestrator('monitor');
await monitor.initialize();

// Subscribe to all status updates
await monitor.client.subscribeStatus('agent.status.#', async (status) => {
  console.log('Status update:', status);
});
```

### Real-Time Dashboard
```javascript
// scripts/monitor.js provides built-in dashboard
import './scripts/monitor.js';

// Displays:
// - Agent health
// - Queue metrics
// - Performance stats
// - Active alerts
```

## Monitoring Components

### 1. Agent Health Tracking
```javascript
const agentHealth = new Map();

// Track heartbeats
await client.subscribeStatus('agent.status.*', (status) => {
  const { agentId, state } = status.status;

  agentHealth.set(agentId, {
    state,
    lastSeen: Date.now(),
    healthy: state !== 'disconnected'
  });
});

// Periodic health check
setInterval(() => {
  const now = Date.now();
  const unhealthyAgents = [];

  for (const [agentId, health] of agentHealth.entries()) {
    const elapsed = now - health.lastSeen;

    // No heartbeat for > 60 seconds
    if (elapsed > 60000) {
      unhealthyAgents.push(agentId);
      health.healthy = false;
    }
  }

  if (unhealthyAgents.length > 0) {
    sendAlert({
      type: 'agent_unhealthy',
      agents: unhealthyAgents
    });
  }
}, 30000);
```

### 2. Queue Metrics
```javascript
async function monitorQueues() {
  const queues = ['agent.tasks', 'agent.results'];

  for (const queue of queues) {
    const info = await channel.checkQueue(queue);

    const metrics = {
      queue,
      depth: info.messageCount,
      consumers: info.consumerCount,
      unacked: info.messageCount - info.messagesReady,
      timestamp: Date.now()
    };

    // Store metrics
    await storeMetrics(metrics);

    // Check thresholds
    if (metrics.depth > 100) {
      sendAlert({
        type: 'high_queue_depth',
        queue,
        depth: metrics.depth
      });
    }

    if (metrics.consumers === 0 && metrics.depth > 0) {
      sendAlert({
        type: 'no_consumers',
        queue,
        depth: metrics.depth
      });
    }
  }
}

// Monitor every 10 seconds
setInterval(monitorQueues, 10000);
```

### 3. Performance Metrics
```javascript
class PerformanceTracker {
  constructor() {
    this.durations = [];
    this.startTimes = new Map();
  }

  startTask(taskId) {
    this.startTimes.set(taskId, Date.now());
  }

  endTask(taskId) {
    const start = this.startTimes.get(taskId);
    if (!start) return;

    const duration = Date.now() - start;
    this.durations.push(duration);
    this.startTimes.delete(taskId);

    // Keep last 1000 durations
    if (this.durations.length > 1000) {
      this.durations.shift();
    }
  }

  getStats() {
    if (this.durations.length === 0) return null;

    return {
      count: this.durations.length,
      min: Math.min(...this.durations),
      max: Math.max(...this.durations),
      avg: average(this.durations),
      p50: percentile(this.durations, 50),
      p95: percentile(this.durations, 95),
      p99: percentile(this.durations, 99)
    };
  }
}

const perfTracker = new PerformanceTracker();

// Track task durations
await client.subscribeStatus('agent.status.task.started', (msg) => {
  perfTracker.startTask(msg.status.taskId);
});

await client.subscribeStatus('agent.status.task.completed', (msg) => {
  perfTracker.endTask(msg.status.taskId);
});

// Periodic performance report
setInterval(() => {
  const stats = perfTracker.getStats();
  console.log('Performance:', stats);

  // Alert on degradation
  if (stats && stats.p95 > 10000) {  // 10 seconds
    sendAlert({
      type: 'performance_degradation',
      p95: stats.p95
    });
  }
}, 60000);
```

### 4. Error Tracking
```javascript
const errorTracker = {
  errors: [],
  errorRate: 0,
  lastCheck: Date.now()
};

await client.subscribeStatus('agent.status.task.failed', (msg) => {
  const error = {
    taskId: msg.status.taskId,
    agentId: msg.status.agentId,
    error: msg.status.error,
    timestamp: Date.now()
  };

  errorTracker.errors.push(error);

  // Calculate error rate
  const now = Date.now();
  const recentErrors = errorTracker.errors.filter(e =>
    now - e.timestamp < 300000  // Last 5 minutes
  );

  errorTracker.errorRate = recentErrors.length / 5;  // Per minute

  if (errorTracker.errorRate > 5) {
    sendAlert({
      type: 'high_error_rate',
      rate: errorTracker.errorRate,
      recentErrors: recentErrors.slice(0, 5)
    });
  }
});
```

## Alerting System

### Alert Configuration
```javascript
const alertRules = [
  {
    name: 'high_queue_depth',
    condition: (metrics) => metrics.queueDepth > 100,
    severity: 'warning',
    message: (metrics) => `Queue depth high: ${metrics.queueDepth}`,
    action: async (metrics) => {
      await publishStatus({
        event: 'scale_recommendation',
        message: 'Start additional workers'
      }, 'agent.status.alert');
    }
  },
  {
    name: 'agent_disconnected',
    condition: (metrics) => !metrics.agentHealthy,
    severity: 'critical',
    message: (metrics) => `Agent ${metrics.agentId} disconnected`,
    action: async (metrics) => {
      await publishStatus({
        event: 'agent_failure',
        agentId: metrics.agentId
      }, 'agent.status.alert');
    }
  },
  {
    name: 'high_failure_rate',
    condition: (metrics) => metrics.failureRate > 0.1,
    severity: 'warning',
    message: (metrics) => `Failure rate: ${(metrics.failureRate * 100).toFixed(1)}%`,
    action: async (metrics) => {
      // Investigate and report
    }
  }
];
```

### Alert Execution
```javascript
async function checkAlerts(metrics) {
  for (const rule of alertRules) {
    if (rule.condition(metrics)) {
      const alert = {
        name: rule.name,
        severity: rule.severity,
        message: rule.message(metrics),
        timestamp: Date.now(),
        metrics
      };

      // Store alert
      activeAlerts.set(rule.name, alert);

      // Execute action
      await rule.action(metrics);

      // Log alert
      console.log(`🚨 [${alert.severity.toUpperCase()}] ${alert.message}`);
    } else {
      // Rule no longer triggered, resolve alert
      if (activeAlerts.has(rule.name)) {
        console.log(`✅ Resolved: ${rule.name}`);
        activeAlerts.delete(rule.name);
      }
    }
  }
}
```

## Dashboard

### Console Dashboard
```javascript
function displayDashboard(metrics) {
  console.clear();

  console.log('═══════════════════════════════════════════════════════');
  console.log('📊 MULTI-AGENT ORCHESTRATION SYSTEM MONITOR');
  console.log('═══════════════════════════════════════════════════════\n');

  // Agents
  console.log('🤖 AGENTS');
  console.log(`   Total: ${metrics.agents.total}`);
  console.log(`   Connected: ${metrics.agents.connected} ✅`);
  console.log(`   Disconnected: ${metrics.agents.disconnected} ❌`);
  console.log(`   Active: ${metrics.agents.active} ⚙️`);
  console.log(`   Idle: ${metrics.agents.idle} 💤\n`);

  // Tasks
  console.log('📋 TASKS');
  console.log(`   Queued: ${metrics.tasks.queued}`);
  console.log(`   Active: ${metrics.tasks.active}`);
  console.log(`   Completed: ${metrics.tasks.completed} ✅`);
  console.log(`   Failed: ${metrics.tasks.failed} ❌\n`);

  // Performance
  console.log('⚡ PERFORMANCE (last 5min)');
  console.log(`   Tasks/min: ${metrics.performance.tasksPerMinute.toFixed(1)}`);
  console.log(`   Avg duration: ${metrics.performance.avgDuration.toFixed(1)}s`);
  console.log(`   Success rate: ${(metrics.performance.successRate * 100).toFixed(1)}%\n`);

  // Alerts
  if (metrics.alerts.active > 0) {
    console.log(`🚨 ALERTS: ${metrics.alerts.active} active\n`);

    for (const alert of metrics.alerts.list) {
      const icon = alert.severity === 'critical' ? '⛔' : '⚠️';
      console.log(`   ${icon} ${alert.message}`);
    }
    console.log('');
  }

  console.log(`Last updated: ${new Date().toISOString()}`);
  console.log('═══════════════════════════════════════════════════════');
}

// Update every 2 seconds
setInterval(() => {
  const metrics = collectAllMetrics();
  displayDashboard(metrics);
}, 2000);
```

## Metrics Collection

### Time-Series Data
```javascript
class MetricsCollector {
  constructor() {
    this.timeseries = new Map();
  }

  record(metric, value, timestamp = Date.now()) {
    if (!this.timeseries.has(metric)) {
      this.timeseries.set(metric, []);
    }

    this.timeseries.get(metric).push({ value, timestamp });

    // Keep last hour of data
    this.cleanup(metric, timestamp - 3600000);
  }

  cleanup(metric, before) {
    const series = this.timeseries.get(metric);
    if (!series) return;

    const filtered = series.filter(d => d.timestamp >= before);
    this.timeseries.set(metric, filtered);
  }

  query(metric, start, end = Date.now()) {
    const series = this.timeseries.get(metric) || [];
    return series.filter(d =>
      d.timestamp >= start && d.timestamp <= end
    );
  }

  aggregate(metric, start, end, aggregation = 'avg') {
    const data = this.query(metric, start, end);
    const values = data.map(d => d.value);

    switch (aggregation) {
      case 'avg': return average(values);
      case 'sum': return sum(values);
      case 'min': return Math.min(...values);
      case 'max': return Math.max(...values);
      case 'count': return values.length;
      default: return null;
    }
  }
}

const metrics = new MetricsCollector();

// Record metrics
setInterval(() => {
  metrics.record('queue_depth', queueDepth);
  metrics.record('active_agents', activeAgents.size);
  metrics.record('tasks_per_minute', calculateTaskRate());
}, 10000);

// Query metrics
const last5MinAvg = metrics.aggregate('queue_depth',
  Date.now() - 300000,
  Date.now(),
  'avg'
);
```

## Anomaly Detection

### Statistical Anomaly Detection
```javascript
function detectAnomalies(metric, threshold = 2) {
  const values = metrics.query(metric,
    Date.now() - 3600000  // Last hour
  ).map(d => d.value);

  const mean = average(values);
  const stdDev = standardDeviation(values);

  const latest = values[values.length - 1];
  const zScore = Math.abs((latest - mean) / stdDev);

  if (zScore > threshold) {
    sendAlert({
      type: 'anomaly_detected',
      metric,
      value: latest,
      expected: mean,
      zScore,
      severity: zScore > 3 ? 'critical' : 'warning'
    });
  }
}

// Check for anomalies periodically
setInterval(() => {
  detectAnomalies('queue_depth');
  detectAnomalies('task_duration');
  detectAnomalies('error_rate');
}, 60000);
```

## Health Checks

### System Health Score
```javascript
function calculateHealthScore() {
  let score = 100;

  // Deduct for disconnected agents
  const disconnectedPenalty = (disconnectedAgents / totalAgents) * 30;
  score -= disconnectedPenalty;

  // Deduct for high queue depth
  if (queueDepth > 50) score -= 10;
  if (queueDepth > 100) score -= 20;

  // Deduct for high error rate
  if (errorRate > 0.05) score -= 10;
  if (errorRate > 0.1) score -= 20;

  // Deduct for performance degradation
  if (p95Duration > baseline * 1.5) score -= 10;
  if (p95Duration > baseline * 2) score -= 20;

  return Math.max(0, score);
}

// Report health score
setInterval(() => {
  const score = calculateHealthScore();

  console.log(`Health Score: ${score}/100`);

  if (score < 50) {
    sendAlert({
      type: 'system_unhealthy',
      score,
      severity: 'critical'
    });
  }
}, 60000);
```

## Best Practices

1. **Monitor Continuously**: Run dedicated monitor agent
2. **Set Appropriate Thresholds**: Tune to your workload
3. **Aggregate Metrics**: Store time-series data
4. **Alert Actionably**: Every alert should have clear action
5. **Track Trends**: Look for gradual degradation
6. **Dashboard Visibility**: Keep monitor visible
7. **Historical Analysis**: Review metrics periodically

## Examples

See `examples/monitoring/`:
- `basic-monitoring.js` - Simple health checks
- `dashboard.js` - Real-time dashboard
- `alerting.js` - Alert configuration
- `anomaly-detection.js` - Statistical anomalies
- `metrics-export.js` - Export to external systems

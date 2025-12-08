---
name: result-aggregation
description: Collect and synthesize results from multiple agents into cohesive outputs. Use for combining work from parallel executions or brainstorming sessions.
---

# Result Aggregation

Collect, combine, and synthesize results from distributed agent execution.

## Quick Start

### Basic Result Collection
```javascript
const results = [];

await client.consumeResults('agent.results', async (msg) => {
  results.push(msg.result);

  console.log(`Received result ${results.length}`);
});
```

### Wait for All Results
```javascript
async function collectAllResults(taskIds) {
  const results = new Map();

  return new Promise((resolve) => {
    client.consumeResults('agent.results', async (msg) => {
      const { taskId, result } = msg.result;

      results.set(taskId, result);

      // Check if all results received
      if (results.size === taskIds.length) {
        resolve(Array.from(results.values()));
      }
    });
  });
}
```

## Aggregation Patterns

### Pattern 1: Collect and Merge
Combine all results into single output.

```javascript
async function collectAndMerge(taskCount) {
  const results = [];

  await consumeResults('agent.results', async (msg) => {
    results.push(msg.result);

    if (results.length === taskCount) {
      // All results received, merge them
      const merged = mergeResults(results);
      console.log('Final result:', merged);
    }
  });
}

function mergeResults(results) {
  // Example: Merge test results
  return {
    totalTests: sum(results.map(r => r.tests)),
    passed: sum(results.map(r => r.passed)),
    failed: sum(results.map(r => r.failed)),
    duration: max(results.map(r => r.duration)),
    coverage: average(results.map(r => r.coverage))
  };
}
```

### Pattern 2: Map-Reduce
Process results in stages.

```javascript
// Map phase: Distribute work
const chunks = splitData(largeDataset, 10);
for (const chunk of chunks) {
  await assignTask({ type: 'map', data: chunk });
}

// Intermediate collect
const mapResults = await collectResults(chunks.length);

// Reduce phase: Aggregate
const finalResult = reduceResults(mapResults);

function reduceResults(mapResults) {
  return mapResults.reduce((acc, result) => {
    // Combine results
    Object.keys(result).forEach(key => {
      acc[key] = (acc[key] || 0) + result[key];
    });
    return acc;
  }, {});
}
```

### Pattern 3: Streaming Aggregation
Process results as they arrive.

```javascript
let partialResult = initializeResult();

await consumeResults('agent.results', async (msg) => {
  // Update partial result immediately
  partialResult = updateResult(partialResult, msg.result);

  // Display running total
  console.log('Current status:', partialResult);

  // Publish intermediate results
  await publishStatus({
    event: 'progress_update',
    partial: partialResult
  });
});
```

### Pattern 4: Quorum-Based
Wait for majority, not all results.

```javascript
async function quorumAggregation(totalAgents, quorum = 0.6) {
  const results = [];
  const requiredResults = Math.ceil(totalAgents * quorum);

  await consumeResults('agent.results', async (msg) => {
    results.push(msg.result);

    if (results.length >= requiredResults) {
      // Got quorum, can proceed
      const consensusResult = buildConsensus(results);
      return consensusResult;
    }
  });
}
```

## Result Synthesis

### Synthesize Brainstorm Responses
```javascript
function synthesizeBrainstorm(responses) {
  // Extract all suggestions
  const allSuggestions = responses.flatMap(r =>
    r.response.recommendation
  );

  // Find common themes
  const themes = extractThemes(allSuggestions);

  // Calculate support for each theme
  const themesWithSupport = themes.map(theme => ({
    theme,
    support: calculateSupport(theme, responses),
    agents: findSupportingAgents(theme, responses)
  }));

  // Sort by support
  themesWithSupport.sort((a, b) => b.support - a.support);

  // Identify consensus
  const consensus = themesWithSupport[0].support > 0.7
    ? 'STRONG'
    : themesWithSupport[0].support > 0.5
    ? 'MODERATE'
    : 'WEAK';

  return {
    consensus,
    majorityView: themesWithSupport[0],
    allThemes: themesWithSupport,
    conflicts: identifyConflicts(responses),
    synthesis: synthesizeRecommendation(themesWithSupport)
  };
}
```

### Combine Test Results
```javascript
function aggregateTestResults(results) {
  const combined = {
    suites: [],
    totals: {
      tests: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      duration: 0
    },
    coverage: {
      lines: 0,
      functions: 0,
      branches: 0,
      statements: 0
    }
  };

  for (const result of results) {
    // Combine test suites
    combined.suites.push(...result.suites);

    // Sum totals
    combined.totals.tests += result.totals.tests;
    combined.totals.passed += result.totals.passed;
    combined.totals.failed += result.totals.failed;
    combined.totals.skipped += result.totals.skipped;
    combined.totals.duration = Math.max(
      combined.totals.duration,
      result.totals.duration
    );

    // Average coverage
    Object.keys(combined.coverage).forEach(key => {
      combined.coverage[key] += result.coverage[key];
    });
  }

  // Calculate average coverage
  const count = results.length;
  Object.keys(combined.coverage).forEach(key => {
    combined.coverage[key] /= count;
  });

  return combined;
}
```

### Merge Code Analysis Results
```javascript
function mergeAnalysisResults(results) {
  const merged = {
    issues: [],
    metrics: {},
    suggestions: []
  };

  for (const result of results) {
    // Combine issues (deduplicate)
    const newIssues = result.issues.filter(issue =>
      !merged.issues.some(existing =>
        isSameIssue(existing, issue)
      )
    );
    merged.issues.push(...newIssues);

    // Merge metrics
    Object.keys(result.metrics).forEach(key => {
      if (!merged.metrics[key]) {
        merged.metrics[key] = [];
      }
      merged.metrics[key].push(result.metrics[key]);
    });

    // Combine suggestions (deduplicate)
    const newSuggestions = result.suggestions.filter(s =>
      !merged.suggestions.includes(s)
    );
    merged.suggestions.push(...newSuggestions);
  }

  // Aggregate metrics
  Object.keys(merged.metrics).forEach(key => {
    const values = merged.metrics[key];
    merged.metrics[key] = {
      min: Math.min(...values),
      max: Math.max(...values),
      avg: average(values),
      total: sum(values)
    };
  });

  // Prioritize issues and suggestions
  merged.issues.sort((a, b) => b.severity - a.severity);
  merged.suggestions = dedupAndPrioritize(merged.suggestions);

  return merged;
}
```

## Statistical Aggregation

### Calculate Statistics
```javascript
function calculateStatistics(results) {
  const values = results.map(r => r.value);

  return {
    count: values.length,
    sum: sum(values),
    min: Math.min(...values),
    max: Math.max(...values),
    mean: average(values),
    median: median(values),
    mode: mode(values),
    stdDev: standardDeviation(values),
    variance: variance(values),
    percentiles: {
      p50: percentile(values, 50),
      p75: percentile(values, 75),
      p90: percentile(values, 90),
      p95: percentile(values, 95),
      p99: percentile(values, 99)
    }
  };
}
```

### Outlier Detection
```javascript
function detectOutliers(results) {
  const stats = calculateStatistics(results);

  const outliers = results.filter(r => {
    const zScore = Math.abs((r.value - stats.mean) / stats.stdDev);
    return zScore > 2;  // More than 2 standard deviations
  });

  return {
    outliers,
    cleanResults: results.filter(r => !outliers.includes(r)),
    stats: calculateStatistics(
      results.filter(r => !outliers.includes(r))
    )
  };
}
```

## Timeout and Partial Results

### Handle Incomplete Results
```javascript
async function collectWithTimeout(taskCount, timeout = 60000) {
  const results = [];
  const startTime = Date.now();

  return new Promise((resolve) => {
    const timeoutId = setTimeout(() => {
      console.warn(`⏰ Timeout: Only ${results.length}/${taskCount} results received`);

      // Return partial results
      resolve({
        complete: false,
        received: results.length,
        expected: taskCount,
        results: results,
        missing: taskCount - results.length
      });
    }, timeout);

    consumeResults('agent.results', async (msg) => {
      results.push(msg.result);

      if (results.length === taskCount) {
        clearTimeout(timeoutId);
        resolve({
          complete: true,
          results: results
        });
      }
    });
  });
}
```

### Progressive Disclosure
```javascript
// Show results as they arrive
async function progressiveAggregation(taskCount) {
  const results = [];
  let lastUpdate = Date.now();

  await consumeResults('agent.results', async (msg) => {
    results.push(msg.result);

    // Update every 2 seconds or when complete
    const now = Date.now();
    if (now - lastUpdate > 2000 || results.length === taskCount) {
      lastUpdate = now;

      const partial = aggregatePartial(results);
      console.log(`Progress: ${results.length}/${taskCount}`);
      console.log('Current results:', partial);

      // Publish progress
      await publishStatus({
        event: 'aggregation_progress',
        progress: results.length / taskCount,
        partial
      });
    }

    if (results.length === taskCount) {
      const final = aggregateFinal(results);
      console.log('Final results:', final);
    }
  });
}
```

## Weighted Aggregation

### Weight by Confidence
```javascript
function weightedAggregation(responses) {
  // Weight each response by its confidence score
  const totalConfidence = sum(responses.map(r => r.confidence));

  const weighted = responses.map(r => ({
    ...r,
    weight: r.confidence / totalConfidence
  }));

  // Calculate weighted average recommendation
  const recommendation = buildWeightedRecommendation(weighted);

  return {
    recommendation,
    confidence: average(responses.map(r => r.confidence)),
    responses: weighted
  };
}
```

### Weight by Agent Expertise
```javascript
function expertiseWeightedAggregation(responses, agentExpertise) {
  const weighted = responses.map(r => {
    const expertise = agentExpertise[r.from] || 0.5;
    return {
      ...r,
      weight: expertise
    };
  });

  return buildWeightedRecommendation(weighted);
}
```

## Deduplication

### Deduplicate Results
```javascript
function deduplicateResults(results) {
  const seen = new Set();
  const unique = [];

  for (const result of results) {
    const key = generateResultKey(result);

    if (!seen.has(key)) {
      seen.add(key);
      unique.push(result);
    }
  }

  return unique;
}

function generateResultKey(result) {
  // Create unique key based on result content
  const normalized = JSON.stringify(result, Object.keys(result).sort());
  return hash(normalized);
}
```

## Error Handling

### Handle Failed Results
```javascript
async function aggregateWithErrorHandling(taskIds) {
  const results = [];
  const errors = [];

  await consumeResults('agent.results', async (msg) => {
    const { result } = msg;

    if (result.status === 'error') {
      errors.push(result);
      console.error(`Task ${result.taskId} failed:`, result.error);
    } else {
      results.push(result);
    }

    if (results.length + errors.length === taskIds.length) {
      // All tasks complete (success or failure)
      const aggregated = aggregateSuccessfulResults(results);

      return {
        success: results.length,
        failed: errors.length,
        results: aggregated,
        errors: errors
      };
    }
  });
}
```

## Best Practices

1. **Set Timeouts**: Don't wait indefinitely for results
2. **Handle Partial Results**: Gracefully handle incomplete data
3. **Deduplicate**: Remove duplicate results
4. **Validate**: Check result integrity before aggregating
5. **Progressive Updates**: Show results as they arrive
6. **Error Handling**: Account for failed tasks
7. **Weighted Aggregation**: Consider confidence/expertise
8. **Single Consumer Pattern**: Only ONE consumer type per queue (see below)

---

## Critical Architecture Warning

**Result Queue Consumer Conflict (December 7, 2025)**

The `agent.results` queue should have a SINGLE consumer pattern:

```
PROBLEM: Multiple consumer types on same queue
+-------------------+
| agent.results     |
+-------------------+
    /           \
   v             v
Leader         Worker
(task results) (brainstorm)

CONFLICT! Messages go to random consumer!
```

**Solution Pattern:**
```
CORRECT: Separate queues for separate purposes
+-------------------+     +---------------------------+
| agent.results     |     | agent.brainstorm.results  |
+-------------------+     +---------------------------+
         |                           |
         v                           v
      Leader                      Workers
   (task results)            (brainstorm responses)
```

**Before aggregating results, verify:**
- [ ] Only intended consumers listen to the queue
- [ ] No competing consumers for same message type
- [ ] Message routing is deterministic

See: `docs/lessons/LESSONS_LEARNED.md` for full analysis

## Examples

See `examples/aggregation/`:
- `map-reduce.js` - Map-reduce pattern
- `streaming.js` - Streaming aggregation
- `quorum.js` - Quorum-based collection
- `weighted.js` - Confidence-weighted synthesis
- `timeout.js` - Handling timeouts and partial results

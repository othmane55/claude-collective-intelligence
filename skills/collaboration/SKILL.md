---
name: agent-collaboration
description: Enable multi-agent brainstorming and collaborative problem-solving using pub/sub messaging. Use for complex decisions requiring multiple perspectives.
---

# Agent Collaboration

Facilitate brainstorming and collaboration across distributed Claude Code agents.

## Quick Start

### Initiate Brainstorm
```javascript
await orchestrator.initiateBrainstorm({
  topic: "API Design",
  question: "REST vs GraphQL vs gRPC?",
  requiredAgents: ["backend", "frontend"]
});
```

### Participate in Brainstorm
```javascript
// Collaborator automatically receives and responds
await client.listenBrainstorm(brainstormQueue, async (msg) => {
  const { topic, question } = msg.message;

  // Analyze and respond
  const response = await analyzeTopic(topic, question);

  await publishResult({
    type: 'brainstorm_response',
    sessionId: msg.message.sessionId,
    suggestion: response
  });
});
```

## Collaboration Patterns

### Pattern 1: Parallel Brainstorming
All agents provide independent input simultaneously.

```javascript
// Initiator broadcasts question
await broadcastBrainstorm({
  topic: "Performance Optimization",
  question: "How to reduce API latency?"
});

// All collaborators respond independently
// Agent 1: "Implement caching"
// Agent 2: "Optimize database queries"
// Agent 3: "Use CDN for static assets"
// Agent 4: "Add read replicas"

// Initiator aggregates all responses
const allResponses = await collectResponses(sessionId, timeout);
const summary = synthesizeResponses(allResponses);
```

### Pattern 2: Sequential Refinement
Each agent builds upon previous responses.

```javascript
// Round 1: Initial proposals
await broadcastRound(1, "Propose architecture");

// Round 2: Critique proposals
const round1Results = await collectRound(1);
await broadcastRound(2, "Critique these proposals", round1Results);

// Round 3: Synthesize
const round2Results = await collectRound(2);
await broadcastRound(3, "Build consensus", round2Results);
```

### Pattern 3: Expert Panel
Targeted collaboration with domain specialists.

```javascript
// Only invite relevant specialists
await broadcastBrainstorm({
  topic: "Database Selection",
  question: "PostgreSQL vs MongoDB?",
  requiredAgents: ["database", "performance", "devops"],
  excludeOthers: true
});

// Only database, performance, and devops agents respond
```

### Pattern 4: Voting/Consensus
Agents vote on options.

```javascript
await broadcastVote({
  question: "Choose state management library",
  options: ["Redux", "Zustand", "Jotai"],
  votingMethod: "plurality"  // or "ranked-choice"
});

// Collect votes
const votes = await collectVotes();

// Tally results
const winner = tallyVotes(votes);
console.log(`Winner: ${winner} with ${votes[winner]} votes`);
```

## Response Structure

### Structured Response
```javascript
{
  type: 'brainstorm_response',
  sessionId: 'uuid',
  from: 'agent-id',
  agentSpecialty: 'backend-architecture',
  timestamp: Date.now(),

  response: {
    // Analysis
    analysis: "Current approach has limitations...",

    // Pros and cons
    pros: [
      "Advantage 1: High performance",
      "Advantage 2: Developer friendly"
    ],
    cons: [
      "Concern 1: Complexity",
      "Concern 2: Learning curve"
    ],

    // Recommendations
    recommendation: "I suggest using GraphQL because...",
    alternatives: [
      "Alternative 1: REST with HATEOAS",
      "Alternative 2: gRPC for internal services"
    ],

    // Confidence
    confidence: 0.85,  // 0-1 scale

    // Priority/Urgency
    priority: "high"
  }
}
```

## Multi-Round Discussions

### Implementing Rounds
```javascript
async function multiRoundBrainstorm(topic, question, rounds = 3) {
  const allResponses = [];

  for (let round = 1; round <= rounds; round++) {
    console.log(`\n🧠 Round ${round}/${rounds}`);

    // Broadcast with previous round context
    await broadcastBrainstorm({
      topic,
      question,
      round,
      previousRound: allResponses[round - 2] || null
    });

    // Collect responses for this round
    const responses = await collectResponses({
      sessionId: generateSessionId(),
      timeout: 60000,
      minResponses: 3
    });

    allResponses.push(responses);

    // Analysis between rounds
    if (round < rounds) {
      const analysis = analyzeRound(responses);
      console.log(`Round ${round} summary:`, analysis);
    }
  }

  // Final synthesis
  return synthesizeAllRounds(allResponses);
}
```

### Round Types

**Round 1: Divergence** (Generate ideas)
```javascript
// Encourage creative, diverse thinking
await broadcastBrainstorm({
  topic: "New feature ideas",
  question: "What features should we add?",
  guidance: "Be creative, no wrong answers"
});
```

**Round 2: Analysis** (Evaluate ideas)
```javascript
// Critical analysis of Round 1 ideas
await broadcastBrainstorm({
  topic: "Evaluate feature proposals",
  question: "Pros/cons of each proposal?",
  context: round1Ideas
});
```

**Round 3: Convergence** (Build consensus)
```javascript
// Synthesize and decide
await broadcastBrainstorm({
  topic: "Final decision",
  question: "Which approach should we take?",
  context: { round1Ideas, round2Analysis }
});
```

## Consensus Building

### Identifying Consensus

```javascript
function buildConsensus(responses) {
  // Extract recommendations
  const recommendations = responses.map(r => r.response.recommendation);

  // Find common themes
  const themes = extractCommonThemes(recommendations);

  // Calculate agreement levels
  const agreement = {
    strongConsensus: themes.filter(t => t.support > 0.8),
    moderateConsensus: themes.filter(t => t.support > 0.5 && t.support <= 0.8),
    noConsensus: themes.filter(t => t.support <= 0.5)
  };

  // Identify conflicts
  const conflicts = findConflicts(recommendations);

  return {
    consensusLevel: calculateConsensusLevel(agreement),
    majorityView: themes[0],  // Highest support
    minorityViews: themes.slice(1),
    conflicts,
    recommendation: buildFinalRecommendation(agreement, conflicts)
  };
}
```

### Consensus Metrics
```javascript
const consensusMetrics = {
  // Strong consensus (>80% agreement)
  STRONG: (responses) => {
    const majority = findMajorityView(responses);
    return majority.percentage > 0.8;
  },

  // Moderate consensus (50-80% agreement)
  MODERATE: (responses) => {
    const majority = findMajorityView(responses);
    return majority.percentage > 0.5 && majority.percentage <= 0.8;
  },

  // No consensus (<50% agreement)
  WEAK: (responses) => {
    const majority = findMajorityView(responses);
    return majority.percentage <= 0.5;
  }
};
```

## Conflict Resolution

### Detecting Conflicts
```javascript
function detectConflicts(responses) {
  const conflicts = [];

  // Pairwise comparison
  for (let i = 0; i < responses.length; i++) {
    for (let j = i + 1; j < responses.length; j++) {
      const conflictScore = compareResponses(
        responses[i],
        responses[j]
      );

      if (conflictScore > 0.5) {
        conflicts.push({
          agents: [responses[i].from, responses[j].from],
          issue: identifyConflictIssue(responses[i], responses[j]),
          severity: conflictScore
        });
      }
    }
  }

  return conflicts;
}
```

### Resolving Conflicts
```javascript
async function resolveConflicts(conflicts) {
  for (const conflict of conflicts) {
    console.log(`⚠️ Conflict detected: ${conflict.issue}`);

    // Strategy 1: Additional round with conflicting parties
    await broadcastBrainstorm({
      topic: "Resolve conflict",
      question: conflict.issue,
      targetAgents: conflict.agents,
      context: { conflict }
    });

    // Strategy 2: Expert adjudication
    const expert = findExpert(conflict.domain);
    const resolution = await askExpert(expert, conflict);

    // Strategy 3: Majority vote
    const vote = await conductVote(conflict.options);

    // Strategy 4: Leader decision
    const leaderDecision = await escalateToLeader(conflict);
  }
}
```

## Specialized Collaboration

### Domain-Specific Collaboration
```javascript
// Only backend specialists discuss
await broadcastBrainstorm({
  topic: "Database optimization",
  specialtyFilter: "backend",
  minExpertiseLevel: 0.7
});

// Cross-domain collaboration
await broadcastBrainstorm({
  topic: "Full-stack architecture",
  requiredSpecialties: ["backend", "frontend", "devops"],
  minPerSpecialty: 1  // At least one from each
});
```

### Role-Based Collaboration
```javascript
const roles = {
  PROPOSER: "proposes initial ideas",
  CRITIC: "identifies flaws and risks",
  SYNTHESIZER: "combines ideas into solution",
  VALIDATOR: "verifies feasibility"
};

// Assign roles
await broadcastWithRoles({
  topic: "System redesign",
  roles: {
    proposer: ["agent-1", "agent-2"],
    critic: ["agent-3"],
    synthesizer: ["agent-4"],
    validator: ["agent-5"]
  }
});
```

## Timing and Synchronization

### Timeout Management
```javascript
async function collectResponses(sessionId, options = {}) {
  const {
    timeout = 60000,          // Max wait time
    minResponses = 1,         // Minimum required
    maxResponses = Infinity   // Maximum to collect
  } = options;

  const responses = [];
  const startTime = Date.now();

  return new Promise((resolve) => {
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;

      // Timeout reached
      if (elapsed >= timeout) {
        clearInterval(interval);
        console.log(`⏰ Timeout: Collected ${responses.length} responses`);
        resolve(responses);
      }

      // Got enough responses
      if (responses.length >= minResponses &&
          responses.length >= maxResponses) {
        clearInterval(interval);
        console.log(`✅ Collected ${responses.length} responses`);
        resolve(responses);
      }
    }, 1000);

    // Listen for responses
    consumeResults('agent.results', (result) => {
      if (result.sessionId === sessionId) {
        responses.push(result);
      }
    });
  });
}
```

### Synchronization Barriers
```javascript
// Wait for all required agents
async function waitForAllAgents(requiredAgents) {
  const ready = new Set();

  await subscribeStatus('agent.status.ready', (status) => {
    if (requiredAgents.includes(status.agentId)) {
      ready.add(status.agentId);
    }
  });

  // Wait until all are ready
  while (ready.size < requiredAgents.length) {
    await sleep(1000);
  }

  console.log('✅ All agents ready for collaboration');
}
```

## Best Practices

1. **Clear Questions**: Ask specific, answerable questions
2. **Appropriate Timeout**: Balance wait time vs response quality
3. **Target Relevant Experts**: Don't spam all agents
4. **Multi-Round for Complex**: Use rounds for complex decisions
5. **Document Consensus**: Save brainstorm results
6. **Implement Follow-Up**: Act on brainstorm outcomes
7. **Track Metrics**: Monitor collaboration effectiveness

## Examples

See `examples/collaboration/`:
- `parallel-brainstorm.js` - Independent analysis
- `sequential-refinement.js` - Multi-round discussion
- `expert-panel.js` - Targeted specialists
- `consensus-building.js` - Agreement mechanisms
- `conflict-resolution.js` - Handling disagreements

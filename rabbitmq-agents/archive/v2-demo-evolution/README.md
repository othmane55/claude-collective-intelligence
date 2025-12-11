# Archive: Demo Evolution (v1 to v3)

**Status:** SUPERSEDED by Demo 3 (System Inspector v6.0.0)
**Date Archived:** 2025-12-11

## Why Archived?

Demo-1 and Demo-2 were evolutionary steps toward Demo 3.
All patterns have been incorporated into Demo 3's orchestrator.js and role_prompter.py.

## Evolution Timeline

```
Demo 1: Role Assignment        Demo 2: Real Claude Role       Demo 3: System Inspector
(Python pika)                  (Python + CLAUDE.md)           (Node.js + Claude Code)
       │                              │                              │
       ▼                              ▼                              ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│ role_sender.py   │   ──►   │ assign_role.py   │   ──►   │ role_prompter.py │
│ role_receiver.py │         │ wait_for_role.py │         │ orchestrator.js  │
│ config.py        │         │ CLAUDE.md        │         │ run_demo.py      │
└──────────────────┘         └──────────────────┘         └──────────────────┘
     Basic RPC                Sub-Claude Ready              Full Orchestration
```

## Valuable Patterns Preserved

### 1. Role Assignment Message Format (Demo-1)

```json
{
  "role": "Team Leader",
  "agent": "guardian",
  "timestamp": "2025-12-11T03:30:00",
  "assigned_by": "main_claude"
}
```

### 2. Acknowledgment Pattern (Demo-1 & Demo-2)

```json
{
  "status": "accepted",
  "agent": "guardian",
  "role": "Team Leader",
  "message": "Role accepted and activated",
  "timestamp": "2025-12-11T03:30:01"
}
```

### 3. Sub-Claude CLAUDE.md Pattern (Demo-2)

```markdown
## Startup Task
1. Connect to RabbitMQ and listen to `role.assignments`
2. When role message arrives: Accept, Acknowledge, Start working
3. Wait until role is assigned
```

### 4. CLI Argument Pattern (Demo-1)

```python
parser = argparse.ArgumentParser(description='Send role assignment')
parser.add_argument('--role', '-r', required=True)
parser.add_argument('--agent', '-a', required=True)
```

### 5. Timeout with Polling Pattern (Demo-2)

```python
start = time.time()
while time.time() - start < 30:
    method, props, body = channel.basic_get(queue, auto_ack=True)
    if body:
        return process(body)
    time.sleep(0.5)
```

## Files in This Archive

### From Demo-1 (demo-1-role-assignment/)

| File | Description |
|------|-------------|
| role_sender.py | Main Claude's tool to send role assignments |
| role_receiver.py | Agent waiting for role assignments |
| config.py | RabbitMQ config and queue names |
| README.md | Architecture documentation |

### From Demo-2 (demo-2-real-claude-role/)

| File | Description |
|------|-------------|
| assign_role.py | Simplified role assignment |
| wait_for_role.py | Sub-Claude role waiter |
| config.py | Shared configuration |
| CLAUDE.md | Sub-Claude instructions |
| startup_prompt.txt | Initial prompt for Sub-Claude |

## Current Implementation

See `/rabbitmq-agents/demos/demo-3-system-inspector/` for the working implementation:

- **orchestrator.js** - Node.js message orchestration (evolved from role_sender.py)
- **role_prompter.py** - Python terminal automation (evolved from assign_role.py)
- **run_demo.py** - Full demo orchestration (replaces wait_for_role.py)

## Lessons Learned

1. **Python pika works but Node.js is simpler** for rapid prototyping
2. **CLAUDE.md pattern** for Sub-Claude instructions is effective
3. **Polling with timeout** is reliable for acknowledgment waiting
4. **Unbuffered Python output** (`PYTHONUNBUFFERED=1`) is critical for real-time feedback
5. **Argparse CLI** makes tools reusable

## Migration Notes

When upgrading from Demo-1/Demo-2 to Demo-3:

1. Replace `pika` with `amqplib` (Node.js)
2. Use `orchestrator.js` instead of `role_sender.py`
3. Use `role_prompter.py` for terminal automation
4. Keep message format compatible (JSON structure unchanged)


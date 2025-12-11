# Demo 1: RabbitMQ Role Assignment

## Purpose
Demonstrate how Main Claude can assign roles to agents via RabbitMQ and receive acknowledgments.

## Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│    MAIN CLAUDE      │         │   ROLE RECEIVER     │
│   (role_sender.py)  │         │ (role_receiver.py)  │
└──────────┬──────────┘         └──────────┬──────────┘
           │                               │
           │  1. Send Role                 │
           │  ─────────────────────────►   │
           │  (queue: role.assignments)    │
           │                               │
           │                               │ 2. Process Role
           │                               │
           │  3. Acknowledge               │
           │  ◄─────────────────────────   │
           │  (queue: role.acknowledgments)│
           │                               │
           ▼                               ▼
      ┌─────────────────────────────────────────┐
      │              RabbitMQ                    │
      │  - role.assignments (Main → Agent)      │
      │  - role.acknowledgments (Agent → Main)  │
      └─────────────────────────────────────────┘
```

## Files
- `role_receiver.py` - Agent that waits for role assignments
- `role_sender.py` - Script to send roles (used by Main Claude)
- `config.py` - Shared configuration

## Usage

### Step 1: Start Role Receiver (in separate terminal)
```bash
python3 role_receiver.py
```

### Step 2: Send Role Assignment (from Main Claude)
```bash
python3 role_sender.py --role "Team Leader" --agent "guardian"
```

### Step 3: Observe
- Role Receiver prints: "Role received: Team Leader"
- Main Claude receives: "Acknowledgment: guardian accepted role Team Leader"

## Message Format

### Role Assignment
```json
{
  "role": "Team Leader",
  "agent": "guardian",
  "timestamp": "2025-12-11T03:30:00",
  "assigned_by": "main_claude"
}
```

### Acknowledgment
```json
{
  "status": "accepted",
  "agent": "guardian",
  "role": "Team Leader",
  "message": "Role accepted and activated",
  "timestamp": "2025-12-11T03:30:01"
}
```

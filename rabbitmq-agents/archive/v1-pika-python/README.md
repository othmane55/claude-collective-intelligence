# Archive: v1 Pika-Python Implementation

**Status:** SUPERSEDED by Demo 3 (Node.js orchestrator)
**Date Archived:** 2025-12-11

## Why Archived?

This was the first attempt at a multi-agent RabbitMQ system using Python + pika.
It was replaced by Demo 3 which uses Node.js orchestrator + Claude Code terminals.

## Valuable Patterns to Preserve

### 1. Second Monitor Detection (easy_connect.py)

```python
def get_second_monitor_info():
    from AppKit import NSScreen
    screens = NSScreen.screens()
    if len(screens) >= 2:
        frame = screens[1].frame()
        return {
            'x': int(frame.origin.x),
            'y': int(frame.origin.y),
            'width': int(frame.size.width),
            'height': int(frame.size.height)
        }
    return {'x': 1280, 'y': 0, 'width': 1920, 'height': 1080}  # Fallback
```

### 2. Plugin Validation Error Codes (worker_manifest.py)

| Code | Error | Description |
|------|-------|-------------|
| E001 | Structure | .claude-plugin is FILE not DIRECTORY |
| E002 | Location | plugin.json at wrong location |
| E003 | Placement | Components inside .claude-plugin/ |
| E102 | Frontmatter | Starts with '>---' instead of '---' |
| E103 | Frontmatter | Missing YAML frontmatter |
| E201 | Config | Shell expansion in JSON files |
| E301 | Schema | Directory path instead of file paths |
| E303 | Collision | marketplace.name = plugin.name |
| E404 | Structure | Nested metadata in frontmatter |

### 3. Skeptical Review Pattern (guardian_leader.py)

```python
# Guardian's skeptical validation
if status == 'success':
    print("[TRUST BUT VERIFY] Result accepted pending evidence")
else:
    print("[ALERT] Task failed - investigation required")
```

### 4. RabbitMQ Connection Pattern (config.py)

```python
RABBITMQ_CONFIG = {
    'host': 'localhost',
    'port': 5672,
    'virtual_host': '/',
    'credentials': {
        'username': 'admin',      # NOT guest!
        'password': 'rabbitmq123'
    }
}
```

## Files in This Archive

| File | Description |
|------|-------------|
| config.py | RabbitMQ config + agent definitions |
| easy_connect.py | Terminal launcher with monitor detection |
| guardian_leader.py | Team Leader (pika-based) |
| worker_lifecycle.py | Plugin lifecycle operations |
| worker_manifest.py | Plugin validation worker |
| launch_all.sh | VS Code terminal launcher |
| requirements.txt | Python dependencies (pika, colorama) |

## Current Implementation

See `/rabbitmq-agents/demos/demo-3-system-inspector/` for the working implementation using:
- Node.js orchestrator.js
- Claude Code terminals
- Python orchestrator.py for terminal automation

## Lessons Learned

1. **Pika works but Node.js is simpler** for Claude Code integration
2. **Monitor detection via AppKit** is reliable on macOS
3. **Error codes** should be standardized across all validators
4. **Skeptical review** is a valuable pattern for result validation

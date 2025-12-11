# Demo 3: System Inspector - Multi-Agent Terminal Orchestration

## v5.1.0 - Window ID Tracking, RabbitMQ Role Assignment & Safe Shutdown

**WORKING DEMO** - Fully tested and verified on 2025-12-11

## Purpose

Mac dual-monitor setup with automated multi-agent Claude Code orchestration:
1. Detect display configuration
2. Open 3 terminals on external display with Window ID tracking
3. Launch Claude Code in each terminal
4. Assign RabbitMQ roles (Team Leader, Agent, Worker)
5. **NEW:** Safe shutdown - `/exit` to Claude Code, then close terminals

**Two commands to run:**
```bash
# Start pipeline (Task 1-5)
python orchestrator.py

# Safe shutdown (Task Final)
python orchestrator.py --task task_final --load-context
```

## Architecture

```
                        SYSTEM INSPECTOR PIPELINE v5.1.0
==========================================================================

   TASK 1              TASK 2                TASK 3              TASK 4
   Display    ------>  Terminal     ------>  Screenshot  ------>  Claude
   Inspector           Setup                 Validator           Launcher
   (detect)            (open+ID)             (verify)            (launch)
                           |
                           v
                    Window ID Capture
                    [25534, 25536, 25538]
                           |
                           |
                           v
                        TASK 5                    TASK FINAL
                    Role Prompter    ------>   Safe Shutdown
                    (assign roles)             (/exit + close)
                           |                        |
                    +------+------+          +------+------+
                    |      |      |          |      |      |
                    v      v      v          v      v      v
                 LEADER  AGENT  WORKER    /exit   /exit   /exit
                 (25534) (25536) (25538)  close   close   close

==========================================================================
```

## Key Innovation: Window ID Tracking

**Problem:** AppleScript ile 3 terminale mesaj gonderirken hangisinin hangisi oldugunu tespit edemiyorduk.

**Solution:** Terminal acilir acilmaz `id of window 1` ile benzersiz ID yakaliyoruz:
```applescript
do script ""
set currentWindowID to id of window 1  -- HEMEN YAKALA!
```

**Result:** %100 guvenilir terminal hedefleme!

## File Structure

```
demo-3-system-inspector/
├── orchestrator.py              # Main entry point (v5.1.0 with --load-context)
├── run.sh                       # Quick start script
├── config/
│   └── workflow.yaml            # Pipeline configuration v5.1.0
├── tasks/
│   ├── __init__.py
│   ├── base.py                  # Abstract base class
│   ├── display_inspector.py     # Task 1: Display detection
│   ├── terminal_setup.py        # Task 2: Terminal + Window ID
│   ├── screenshot_validator.py  # Task 3: Cross-check
│   ├── claude_launcher.py       # Task 4: Claude Code launch
│   ├── role_prompter.py         # Task 5: RabbitMQ role assignment
│   └── task_final.py            # Task Final: Safe shutdown (NEW!)
├── scripts/
│   └── setup_terminals.scpt     # Auto-generated AppleScript
├── screenshots/
│   ├── external_display_WORKED_2.jpg
│   ├── claude_verification_WORKED_2.jpg
│   ├── response_leader_WORKED_2.jpg
│   ├── response_worker-1_WORKED_2.jpg
│   ├── response_worker-2_WORKED_2.jpg
│   └── role_prompter_final_WORKED_2.jpg
├── reports/
│   ├── pipeline_report_WORKED_2.json    # Task 1-5 execution log
│   └── shutdown_report_WORKED_2.json    # Task Final execution log
├── archive/                     # Previous WORKED files
│   ├── screenshots/
│   └── reports/
├── CLAUDE.md                    # Claude session instructions
├── WORKFLOW.md                  # Detailed design document
└── README.md                    # This file
```

## Quick Start

```bash
# Navigate to demo directory
cd rabbitmq-agents/demos/demo-3-system-inspector

# Run the full pipeline (Task 1-5)
python orchestrator.py

# ... do your work with Claude Code instances ...

# Safe shutdown (Task Final)
python orchestrator.py --task task_final --load-context
```

## Pipeline Output (Actual v5.1.0 Run)

### Task 1-5 (Main Pipeline)
```
======================================================================
SYSTEM INSPECTOR PIPELINE
======================================================================
Workflow: system-inspector-pipeline
Version: 5.1.0
======================================================================

Task: display_inspector
   Found 2 display(s)
   Main: Color LCD (1280x800)
   External: LG FULL HD (1920x1080)
   Task completed in 361ms

Task: terminal_setup
   Opening 3 terminals
   Window IDs captured: 25534,25536,25538
   LEADER -> Window ID: 25534
   WORKER-1 -> Window ID: 25536
   WORKER-2 -> Window ID: 25538
   3 terminals opened with ID tracking!
   Task completed in 3079ms

Task: screenshot_validator
   Screenshot: external_display_WORKED_2.jpg
   Task completed in 1691ms

Task: claude_launcher
   Launching Claude in LEADER (Window ID: 25534)... OK
   Launching Claude in WORKER-1 (Window ID: 25536)... OK
   Launching Claude in WORKER-2 (Window ID: 25538)... OK
   Claude instances launched: 3/3
   Task completed in 20609ms

Task: role_prompter
   ROL ATAMALARI:
   LEADER (ID: 25534) -> Takim Lideri gorevi
   WORKER-1 (ID: 25536) -> Agent gorevi
   WORKER-2 (ID: 25538) -> Worker gorevi

   ROL ATAMA OZETI:
   Roller atandi: 3/3
   Task completed in 54311ms

======================================================================
PIPELINE SUMMARY
======================================================================
   Successful tasks: 5
   Failed tasks: 0
   Total duration: 80.06s
======================================================================
```

### Task Final (Safe Shutdown)
```
======================================================================
SYSTEM INSPECTOR PIPELINE
======================================================================
Version: 5.1.0
Context loaded from: pipeline_report_WORKED_2.json
   LEADER: Window ID 25534
   WORKER-1: Window ID 25536
   WORKER-2: Window ID 25538
======================================================================

Task: task_final
   KAPATMA SIRASI:
   LEADER (ID: 25534) -> /exit -> close terminal
   WORKER-1 (ID: 25536) -> /exit -> close terminal
   WORKER-2 (ID: 25538) -> /exit -> close terminal

   KAPATMA OZETI:
   Basariyla kapatildi: 3/3
      LEADER (ID: 25534) - success
      WORKER-1 (ID: 25536) - success
      WORKER-2 (ID: 25538) - success
   Task completed in 37523ms

======================================================================
PIPELINE SUMMARY
======================================================================
   Successful tasks: 1
   Total duration: 37.54s
======================================================================
```

## Role Assignment Messages

| Terminal | Role | Message |
|----------|------|---------|
| LEADER | Takim Lideri | "Sana Takim Lideri gorevi verecegim, RabbitMQ baglantisi yapip gorevini deklare edeceksin, hazir misin?" |
| WORKER-1 | Agent | "Sana Agent gorevi verecegim, RabbitMQ baglantisi yapip gorevini deklare edeceksin, hazir misin?" |
| WORKER-2 | Worker | "Sana Worker gorevi verecegim, RabbitMQ baglantisi yapip gorevini deklare edeceksin, hazir misin?" |

## Configuration (workflow.yaml v5.1.0)

```yaml
name: "system-inspector-pipeline"
version: "5.1.0"

tasks:
  - name: "display_inspector"
    enabled: true

  - name: "terminal_setup"
    config:
      terminal_count: 3
      terminal_titles: ["LEADER", "WORKER-1", "WORKER-2"]

  - name: "screenshot_validator"
    depends_on: "terminal_setup"

  - name: "claude_launcher"
    config:
      claude_command: "claude --dangerously-skip-permissions"
      wait_between_launches: 7

  - name: "role_prompter"
    config:
      wait_before_typing: 5
      wait_after_enter: 10
      wait_between_terminals: 7

  - name: "task_final"
    enabled: false  # Manuel calistir: --task task_final --load-context
    config:
      wait_before_exit: 2
      wait_after_exit: 5
      wait_before_close: 2
      close_terminal_after: true
```

## CLI Options

```bash
# Run full pipeline (Task 1-5)
python orchestrator.py

# List available tasks
python orchestrator.py --list

# Run specific task only
python orchestrator.py --task display_inspector

# Dry run (show plan without executing)
python orchestrator.py --dry-run

# Safe shutdown with context from last report (NEW!)
python orchestrator.py --task task_final --load-context
```

## Verified Evidence (Immutable Files)

The following files are marked with `chflags uchg` (immutable):

**Screenshots (WORKED_2):**
- `external_display_WORKED_2.jpg` - 3 terminals on external display
- `claude_verification_WORKED_2.jpg` - Claude Code running in all 3
- `response_leader_WORKED_2.jpg` - Leader accepted role
- `response_worker-1_WORKED_2.jpg` - Agent accepted role
- `response_worker-2_WORKED_2.jpg` - Worker accepted role
- `role_prompter_final_WORKED_2.jpg` - Final verification (all roles assigned)

**Reports (WORKED_2):**
- `pipeline_report_WORKED_2.json` - Complete pipeline execution log (Task 1-5)
- `shutdown_report_WORKED_2.json` - Safe shutdown execution log (Task Final)

**Archive (Previous WORKED):**
- `archive/screenshots/` - Previous verified screenshots
- `archive/reports/` - Previous verified reports

## Technical Details

### Window ID Capture (terminal_setup.py)
```python
# AppleScript captures ID immediately after terminal creation
applescript = '''
tell application "Terminal"
    do script ""
    set currentWindowID to id of window 1  -- CAPTURE IMMEDIATELY!
    set end of windowIDs to currentWindowID
    -- then configure bounds, title, colors...
end tell
'''
```

### Window ID Targeting (role_prompter.py & task_final.py)
```python
def _send_prompt_by_window_id(self, window_id: int, message: str):
    applescript = f'''
    tell application "Terminal"
        set targetWindow to window id {window_id}  -- EXACT TARGETING!
        set frontmost of targetWindow to true
        -- keystroke message...
    end tell
    '''
```

### Safe Shutdown (task_final.py)
```python
def _send_exit_command(self, window_id: int) -> bool:
    """Send /exit to Claude Code"""
    applescript = f'''
    tell application "Terminal"
        set targetWindow to window id {window_id}
        set frontmost of targetWindow to true
        tell application "System Events"
            keystroke "/exit"
            keystroke return
        end tell
    end tell
    '''

def _close_terminal_window(self, window_id: int) -> bool:
    """Close terminal window after Claude exits"""
    applescript = f'''
    tell application "Terminal"
        close window id {window_id}
    end tell
    '''
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 5.1.0 | 2025-12-11 | Task Final (safe shutdown), --load-context option |
| 5.0.0 | 2025-12-11 | Window ID tracking, RabbitMQ role assignment |
| 4.0.0 | 2025-12-11 | Added role_prompter task |
| 3.0.0 | 2025-12-11 | Added claude_launcher task |
| 2.0.0 | 2025-12-11 | Added screenshot_validator task |
| 1.0.0 | 2025-12-11 | Initial release with display_inspector and terminal_setup |

---

**Demo 3 - System Inspector Pipeline v5.1.0**
*Part of Claude Collective Intelligence RabbitMQ Demos*
*Fully working and verified on 2025-12-11*

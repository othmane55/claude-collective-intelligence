#!/usr/bin/env python3 -u
"""
Easy Connect - RabbitMQ Multi-Agent System
==========================================
ULTRATHINK Implementation - Compact & Production Ready

One command to rule them all:
  python3 easy_connect.py guardian    # Start Guardian (Team Leader)
  python3 easy_connect.py lifecycle   # Start Lifecycle Worker
  python3 easy_connect.py manifest    # Start Manifest Worker
  python3 easy_connect.py all         # Start all agents
  python3 easy_connect.py status      # Check RabbitMQ status

Fixes:
- Auto-unbuffered output (no more silent workers)
- Heartbeat system (workers announce themselves)
- Non-interactive mode support
- Single entry point for all agents
"""

import sys
import os
import json
import time
import signal
import threading
import subprocess
from datetime import datetime
from pathlib import Path

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import pika
from config import RABBITMQ_CONFIG, QUEUES, AGENTS, colorize

# ============================================================
# CONSTANTS
# ============================================================
HEARTBEAT_INTERVAL = 10  # seconds
SCRIPT_DIR = Path(__file__).parent

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def print_banner(role: str):
    """Print startup banner."""
    banners = {
        'guardian': f"""
{colorize('╔══════════════════════════════════════════════════════════╗', 'cyan')}
{colorize('║', 'cyan')}  {colorize('GUARDIAN AGENT', 'bold')} - Team Leader                          {colorize('║', 'cyan')}
{colorize('║', 'cyan')}  RabbitMQ: {RABBITMQ_CONFIG['host']}:{RABBITMQ_CONFIG['port']}                               {colorize('║', 'cyan')}
{colorize('║', 'cyan')}  Distributes tasks, validates results                     {colorize('║', 'cyan')}
{colorize('╚══════════════════════════════════════════════════════════╝', 'cyan')}
""",
        'lifecycle': f"""
{colorize('╔══════════════════════════════════════════════════════════╗', 'green')}
{colorize('║', 'green')}  {colorize('LIFECYCLE WORKER', 'bold')} - Plugin Operations                 {colorize('║', 'green')}
{colorize('║', 'green')}  RabbitMQ: {RABBITMQ_CONFIG['host']}:{RABBITMQ_CONFIG['port']}                               {colorize('║', 'green')}
{colorize('║', 'green')}  health, diagnose, install, fix, update                   {colorize('║', 'green')}
{colorize('╚══════════════════════════════════════════════════════════╝', 'green')}
""",
        'manifest': f"""
{colorize('╔══════════════════════════════════════════════════════════╗', 'yellow')}
{colorize('║', 'yellow')}  {colorize('MANIFEST WORKER', 'bold')} - Validation Operations              {colorize('║', 'yellow')}
{colorize('║', 'yellow')}  RabbitMQ: {RABBITMQ_CONFIG['host']}:{RABBITMQ_CONFIG['port']}                               {colorize('║', 'yellow')}
{colorize('║', 'yellow')}  validate, check_schema, publication_ready                {colorize('║', 'yellow')}
{colorize('╚══════════════════════════════════════════════════════════╝', 'yellow')}
""",
    }
    print(banners.get(role, ''), flush=True)


def check_rabbitmq() -> bool:
    """Check if RabbitMQ is accessible."""
    try:
        credentials = pika.PlainCredentials(
            RABBITMQ_CONFIG['credentials']['username'],
            RABBITMQ_CONFIG['credentials']['password']
        )
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_CONFIG['host'],
            port=RABBITMQ_CONFIG['port'],
            virtual_host=RABBITMQ_CONFIG['virtual_host'],
            credentials=credentials,
            blocked_connection_timeout=5,
            socket_timeout=5,
        )
        connection = pika.BlockingConnection(parameters)
        connection.close()
        return True
    except Exception as e:
        print(colorize(f"[ERROR] RabbitMQ not accessible: {e}", 'red'), flush=True)
        return False


def get_queue_stats() -> dict:
    """Get queue statistics from RabbitMQ."""
    try:
        result = subprocess.run(
            ['docker', 'exec', 'agent_rabbitmq', 'rabbitmqctl', 'list_queues',
             'name', 'messages', 'consumers', '--formatter=json'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {q['name']: {'messages': q['messages'], 'consumers': q['consumers']}
                    for q in data}
    except Exception:
        pass
    return {}


# ============================================================
# AGENT RUNNERS
# ============================================================

def run_guardian():
    """Run Guardian Agent with heartbeat support."""
    print_banner('guardian')

    if not check_rabbitmq():
        return

    # Import and run guardian
    from guardian_leader import GuardianLeader
    guardian = GuardianLeader()
    guardian.run()


def run_lifecycle():
    """Run Lifecycle Worker with heartbeat."""
    print_banner('lifecycle')

    if not check_rabbitmq():
        return

    # Import and run worker
    from worker_lifecycle import PluginLifecycleWorker
    worker = PluginLifecycleWorker()

    # Start heartbeat thread
    def heartbeat():
        while worker.running:
            try:
                if worker.channel and worker.channel.is_open:
                    worker.channel.basic_publish(
                        exchange=QUEUES['task_exchange'],
                        routing_key='heartbeat.lifecycle',
                        body=json.dumps({
                            'worker': 'lifecycle',
                            'status': 'alive',
                            'tasks_processed': worker.tasks_processed,
                            'timestamp': datetime.now().isoformat()
                        })
                    )
            except Exception:
                pass
            time.sleep(HEARTBEAT_INTERVAL)

    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
    heartbeat_thread.start()

    worker.run()


def run_manifest():
    """Run Manifest Worker with heartbeat."""
    print_banner('manifest')

    if not check_rabbitmq():
        return

    # Import and run worker
    from worker_manifest import PluginManifestWorker
    worker = PluginManifestWorker()

    # Start heartbeat thread
    def heartbeat():
        while worker.running:
            try:
                if worker.channel and worker.channel.is_open:
                    worker.channel.basic_publish(
                        exchange=QUEUES['task_exchange'],
                        routing_key='heartbeat.manifest',
                        body=json.dumps({
                            'worker': 'manifest',
                            'status': 'alive',
                            'tasks_processed': worker.tasks_processed,
                            'timestamp': datetime.now().isoformat()
                        })
                    )
            except Exception:
                pass
            time.sleep(HEARTBEAT_INTERVAL)

    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
    heartbeat_thread.start()

    worker.run()


def get_second_monitor_info():
    """Get second monitor position and size dynamically."""
    try:
        from AppKit import NSScreen
        screens = NSScreen.screens()
        if len(screens) >= 2:
            # İkinci ekran (index 1)
            frame = screens[1].frame()
            return {
                'x': int(frame.origin.x),
                'y': int(frame.origin.y),
                'width': int(frame.size.width),
                'height': int(frame.size.height)
            }
    except ImportError:
        pass
    # Fallback: Varsayılan değerler (MacBook + LG 1080p)
    return {'x': 1280, 'y': 0, 'width': 1920, 'height': 1080}


def run_all():
    """Launch all agents in separate terminals on SECOND MONITOR."""
    print(colorize("\n🚀 Launching Multi-Agent System...\n", 'bold'), flush=True)

    if not check_rabbitmq():
        print(colorize("\n[TIP] Start RabbitMQ: docker start agent_rabbitmq", 'yellow'), flush=True)
        return

    script_path = Path(__file__).absolute()

    # İkinci monitör bilgilerini al
    monitor = get_second_monitor_info()
    print(colorize(f"[INFO] Second monitor: {monitor['width']}x{monitor['height']} at X={monitor['x']}", 'cyan'), flush=True)

    # Terminal boyutları - 1920px / 3 terminal = ~635px her biri (5px gap)
    term_width = 635
    term_height = 1030
    gap = 5

    # Pozisyonlar - Basit ve net hesaplama
    base_x = monitor['x']  # 1280
    x1 = base_x + gap                    # 1285
    x2 = base_x + gap + term_width + gap # 1925 (=1285+640)
    x3 = base_x + gap + (term_width + gap) * 2  # 2565 (=1285+1280)
    y_top = 25


    # AppleScript - İkinci monitörde yan yana 3 terminal (Window ID tracking)
    apple_script = f'''
    tell application "Terminal"
        activate

        -- Terminal 1: Guardian (Sol)
        do script "cd {SCRIPT_DIR} && clear && python3 -u {script_path} guardian"
        set guardianWin to front window
        set bounds of guardianWin to {{{x1}, {y_top}, {x1 + term_width}, {y_top + term_height}}}
        delay 0.5

        -- Terminal 2: Lifecycle (Orta)
        do script "cd {SCRIPT_DIR} && clear && python3 -u {script_path} lifecycle"
        set lifecycleWin to front window
        set bounds of lifecycleWin to {{{x2}, {y_top}, {x2 + term_width}, {y_top + term_height}}}
        delay 0.5

        -- Terminal 3: Manifest (Sağ)
        do script "cd {SCRIPT_DIR} && clear && python3 -u {script_path} manifest"
        set manifestWin to front window
        set bounds of manifestWin to {{{x3}, {y_top}, {x3 + term_width}, {y_top + term_height}}}

    end tell
    '''

    try:
        subprocess.run(['osascript', '-e', apple_script], check=True)
        print(colorize("✅ 3 Terminal windows opened on second monitor!", 'green'), flush=True)
        print(colorize(f"""
┌────────────────────────────────────────────────────────────────────────────┐
│  İKİNCİ MONİTÖR ({monitor['width']}x{monitor['height']})                                        │
│                                                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   GUARDIAN      │  │   LIFECYCLE     │  │   MANIFEST      │            │
│  │   (Team Leader) │  │   (Worker)      │  │   (Worker)      │            │
│  │   CYAN          │  │   GREEN         │  │   YELLOW        │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│       SOL                  ORTA                 SAĞ                        │
└────────────────────────────────────────────────────────────────────────────┘

Guardian Commands:
  > help                          - Show all commands
  > validate plugin <name>        - Validate plugin
  > health <plugin>               - Check health
  > diagnose <plugin>             - Diagnose issues
  > status                        - System status
  > quit                          - Exit
""", 'cyan'), flush=True)
    except Exception as e:
        print(colorize(f"[ERROR] Failed to launch terminals: {e}", 'red'), flush=True)
        print(colorize("\nManual start:", 'yellow'), flush=True)
        print(f"  Terminal 1: python3 -u {script_path} guardian")
        print(f"  Terminal 2: python3 -u {script_path} lifecycle")
        print(f"  Terminal 3: python3 -u {script_path} manifest")


def show_status():
    """Show system status."""
    print(colorize("\n📊 RabbitMQ Multi-Agent System Status\n", 'bold'), flush=True)

    # Check RabbitMQ
    print(colorize("RabbitMQ Connection:", 'cyan'), flush=True)
    if check_rabbitmq():
        print(colorize(f"  ✅ Connected to {RABBITMQ_CONFIG['host']}:{RABBITMQ_CONFIG['port']}", 'green'), flush=True)
    else:
        print(colorize(f"  ❌ Cannot connect", 'red'), flush=True)
        return

    # Get queue stats
    print(colorize("\nQueue Status:", 'cyan'), flush=True)
    stats = get_queue_stats()

    relevant_queues = ['tasks.lifecycle', 'tasks.manifest', 'results.guardian']
    for queue in relevant_queues:
        if queue in stats:
            q = stats[queue]
            status = colorize('●', 'green') if q['consumers'] > 0 else colorize('○', 'yellow')
            print(f"  {status} {queue}: {q['consumers']} consumers, {q['messages']} pending", flush=True)
        else:
            print(f"  {colorize('○', 'red')} {queue}: not found", flush=True)

    print(colorize("\nQuick Start:", 'cyan'), flush=True)
    print("  python3 easy_connect.py all      # Start all agents")
    print("  python3 easy_connect.py guardian # Start only Guardian")
    print()


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) < 2:
        print(colorize("""
Easy Connect - RabbitMQ Multi-Agent System
==========================================

Usage:
  python3 easy_connect.py <command>

Commands:
  guardian   - Start Guardian Agent (Team Leader)
  lifecycle  - Start Lifecycle Worker
  manifest   - Start Manifest Worker
  all        - Launch all agents in separate terminals
  status     - Show system status

Examples:
  python3 easy_connect.py all        # Quick start everything
  python3 easy_connect.py status     # Check what's running
""", 'cyan'), flush=True)
        return

    command = sys.argv[1].lower()

    if command == 'guardian':
        run_guardian()
    elif command == 'lifecycle':
        run_lifecycle()
    elif command == 'manifest':
        run_manifest()
    elif command == 'all':
        run_all()
    elif command == 'status':
        show_status()
    else:
        print(colorize(f"Unknown command: {command}", 'red'), flush=True)
        print("Use: guardian, lifecycle, manifest, all, or status")


if __name__ == '__main__':
    main()

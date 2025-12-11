#!/usr/bin/env python3
"""
Guardian Agent - Team Leader
============================
ULTRATHINK Implementation - ETK Compliant

Role: Receives user commands, distributes tasks to workers via RabbitMQ
Pattern: Skeptical validation of all worker results

Commands:
- validate plugin <path>    - Validate plugin structure
- health <plugin>           - Check plugin health
- diagnose <plugin>         - Diagnose plugin issues
- fix <plugin>              - Auto-fix plugin issues
- list workers              - List connected workers
- status                    - Show system status
- help                      - Show available commands
- quit                      - Exit
"""

import json
import uuid
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional

import pika
from config import (
    RABBITMQ_CONFIG, QUEUES, AGENTS, COMMAND_ROUTING,
    MESSAGE_TYPES, colorize, print_banner
)


class GuardianLeader:
    """Guardian Agent - Team Leader for multi-agent RabbitMQ system."""

    def __init__(self):
        self.agent_config = AGENTS['guardian']
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self.workers: Dict[str, Dict[str, Any]] = {}
        self.pending_tasks: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, Any] = {}
        self.running = True

    def connect(self) -> bool:
        """Connect to RabbitMQ broker."""
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
                heartbeat=60,
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare exchange
            self.channel.exchange_declare(
                exchange=QUEUES['task_exchange'],
                exchange_type='topic',
                durable=True
            )

            # Declare queues
            for queue_name in [
                QUEUES['task_queue_lifecycle'],
                QUEUES['task_queue_manifest'],
                QUEUES['result_queue'],
                QUEUES['broadcast_queue'],
            ]:
                self.channel.queue_declare(queue=queue_name, durable=True)

            # Bind result queue
            self.channel.queue_bind(
                exchange=QUEUES['task_exchange'],
                queue=QUEUES['result_queue'],
                routing_key='results.*'
            )

            # Bind task queues
            self.channel.queue_bind(
                exchange=QUEUES['task_exchange'],
                queue=QUEUES['task_queue_lifecycle'],
                routing_key='tasks.lifecycle'
            )
            self.channel.queue_bind(
                exchange=QUEUES['task_exchange'],
                queue=QUEUES['task_queue_manifest'],
                routing_key='tasks.manifest'
            )

            print(colorize("[OK] Connected to RabbitMQ", 'green'))
            return True

        except pika.exceptions.AMQPConnectionError as e:
            print(colorize(f"[ERROR] Failed to connect to RabbitMQ: {e}", 'red'))
            return False

    def start_result_listener(self):
        """Start background thread to listen for results."""
        def listener():
            try:
                # Create separate connection for listener
                credentials = pika.PlainCredentials(
                    RABBITMQ_CONFIG['credentials']['username'],
                    RABBITMQ_CONFIG['credentials']['password']
                )
                parameters = pika.ConnectionParameters(
                    host=RABBITMQ_CONFIG['host'],
                    port=RABBITMQ_CONFIG['port'],
                    virtual_host=RABBITMQ_CONFIG['virtual_host'],
                    credentials=credentials,
                    heartbeat=60,
                )
                listener_connection = pika.BlockingConnection(parameters)
                listener_channel = listener_connection.channel()

                def callback(ch, method, properties, body):
                    try:
                        message = json.loads(body.decode())
                        self.handle_result(message)
                    except json.JSONDecodeError:
                        print(colorize(f"[WARN] Invalid JSON received", 'yellow'))
                    ch.basic_ack(delivery_tag=method.delivery_tag)

                listener_channel.basic_consume(
                    queue=QUEUES['result_queue'],
                    on_message_callback=callback,
                    auto_ack=False
                )

                while self.running:
                    listener_connection.process_data_events(time_limit=1)

                listener_connection.close()

            except Exception as e:
                print(colorize(f"[ERROR] Result listener: {e}", 'red'))

        thread = threading.Thread(target=listener, daemon=True)
        thread.start()
        print(colorize("[OK] Result listener started", 'green'))

    def handle_result(self, message: Dict[str, Any]):
        """Handle result from worker (with skeptical validation)."""
        task_id = message.get('task_id')
        worker = message.get('worker')
        status = message.get('status')
        result = message.get('result', {})

        # Store result
        self.results[task_id] = message

        # Remove from pending
        if task_id in self.pending_tasks:
            del self.pending_tasks[task_id]

        # Print result with skeptical review
        print("\n")
        print(colorize("=" * 60, 'cyan'))
        print(colorize(f"  RESULT FROM: {worker}", 'bold'))
        print(colorize("=" * 60, 'cyan'))
        print(f"  Task ID: {task_id}")
        print(f"  Status: {colorize(status, 'green' if status == 'success' else 'red')}")

        if result:
            print(f"\n  {colorize('Result:', 'yellow')}")
            for key, value in result.items():
                print(f"    {key}: {value}")

        # Skeptical validation
        print(f"\n  {colorize('SKEPTICAL REVIEW:', 'magenta')}")
        if status == 'success':
            print(f"    {colorize('[TRUST BUT VERIFY] Result accepted pending evidence', 'yellow')}")
        else:
            print(f"    {colorize('[ALERT] Task failed - investigation required', 'red')}")

        print(colorize("=" * 60, 'cyan'))
        print("\n> ", end='', flush=True)

    def send_task(self, worker_type: str, command: str, params: Dict[str, Any]) -> str:
        """Send task to specific worker."""
        task_id = str(uuid.uuid4())[:8]

        task_message = {
            'type': MESSAGE_TYPES['TASK'],
            'task_id': task_id,
            'command': command,
            'params': params,
            'assigned_worker': worker_type,
            'priority': 1,
            'timestamp': datetime.now().isoformat(),
            'from': self.agent_config['id'],
        }

        routing_key = f"tasks.{worker_type}"

        self.channel.basic_publish(
            exchange=QUEUES['task_exchange'],
            routing_key=routing_key,
            body=json.dumps(task_message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent
                content_type='application/json',
            )
        )

        self.pending_tasks[task_id] = task_message

        print(colorize(f"[SENT] Task {task_id} -> {worker_type}", 'green'))
        return task_id

    def broadcast(self, message: str):
        """Broadcast message to all workers."""
        broadcast_msg = {
            'type': MESSAGE_TYPES['BROADCAST'],
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'from': self.agent_config['id'],
        }

        self.channel.basic_publish(
            exchange=QUEUES['task_exchange'],
            routing_key='broadcast.all',
            body=json.dumps(broadcast_msg),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        print(colorize(f"[BROADCAST] {message}", 'magenta'))

    def parse_command(self, user_input: str) -> tuple:
        """Parse user command into action and parameters."""
        parts = user_input.strip().split()
        if not parts:
            return None, {}

        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        return cmd, args

    def execute_command(self, cmd: str, args: list):
        """Execute user command."""
        if cmd == 'help':
            self.show_help()

        elif cmd == 'quit' or cmd == 'exit':
            self.running = False
            print(colorize("\nGoodbye! Shutting down Guardian...", 'cyan'))

        elif cmd == 'list':
            if args and args[0] == 'workers':
                self.list_workers()
            else:
                print("Usage: list workers")

        elif cmd == 'status':
            self.show_status()

        elif cmd == 'validate':
            if len(args) >= 2:
                target_type = args[0]  # 'plugin' or 'manifest'
                path = args[1]
                self.send_task('manifest', 'validate', {
                    'type': target_type,
                    'path': path
                })
            else:
                print("Usage: validate plugin <path>")

        elif cmd == 'health':
            if args:
                plugin_name = args[0]
                self.send_task('lifecycle', 'health', {
                    'plugin': plugin_name
                })
            else:
                print("Usage: health <plugin-name>")

        elif cmd == 'diagnose':
            if args:
                plugin_name = args[0]
                self.send_task('lifecycle', 'diagnose', {
                    'plugin': plugin_name
                })
            else:
                print("Usage: diagnose <plugin-name>")

        elif cmd == 'fix':
            if args:
                plugin_name = args[0]
                self.send_task('lifecycle', 'fix', {
                    'plugin': plugin_name
                })
            else:
                print("Usage: fix <plugin-name>")

        elif cmd == 'install':
            if args:
                path = args[0]
                self.send_task('lifecycle', 'install', {
                    'path': path
                })
            else:
                print("Usage: install <plugin-path>")

        elif cmd == 'broadcast':
            if args:
                message = ' '.join(args)
                self.broadcast(message)
            else:
                print("Usage: broadcast <message>")

        else:
            print(colorize(f"Unknown command: {cmd}. Type 'help' for available commands.", 'yellow'))

    def show_help(self):
        """Show available commands."""
        help_text = f"""
{colorize('GUARDIAN AGENT - AVAILABLE COMMANDS', 'cyan')}
{colorize('='*50, 'cyan')}

{colorize('Task Distribution:', 'yellow')}
  validate plugin <path>  - Validate plugin structure (-> Manifest Worker)
  health <plugin>         - Check plugin health (-> Lifecycle Worker)
  diagnose <plugin>       - Diagnose issues (-> Lifecycle Worker)
  fix <plugin>            - Auto-fix issues (-> Lifecycle Worker)
  install <path>          - Install plugin (-> Lifecycle Worker)

{colorize('System Commands:', 'yellow')}
  list workers            - List connected workers
  status                  - Show system status
  broadcast <message>     - Send message to all workers

{colorize('General:', 'yellow')}
  help                    - Show this help
  quit                    - Exit Guardian
"""
        print(help_text)

    def list_workers(self):
        """List registered workers."""
        print(f"\n{colorize('REGISTERED WORKERS', 'cyan')}")
        print(colorize("="*40, 'cyan'))

        for worker_type, config in AGENTS.items():
            if worker_type != 'guardian':
                status = colorize("[CONFIGURED]", 'yellow')
                print(f"  {colorize(config['name'], 'bold')}")
                print(f"    ID: {config['id']}")
                print(f"    Role: {config['role']}")
                print(f"    Queue: tasks.{worker_type}")
                print(f"    Status: {status}")
                print()

    def show_status(self):
        """Show system status."""
        print(f"\n{colorize('SYSTEM STATUS', 'cyan')}")
        print(colorize("="*40, 'cyan'))
        print(f"  Guardian: {colorize('ACTIVE', 'green')}")
        print(f"  RabbitMQ: {RABBITMQ_CONFIG['host']}:{RABBITMQ_CONFIG['port']}")
        print(f"  Pending Tasks: {len(self.pending_tasks)}")
        print(f"  Completed Tasks: {len(self.results)}")
        print()

    def run(self):
        """Main run loop."""
        print_banner(
            self.agent_config['name'],
            self.agent_config['role'],
            self.agent_config['color']
        )

        if not self.connect():
            return

        self.start_result_listener()

        print(colorize("\nGuardian Agent ready. Type 'help' for commands.\n", 'green'))

        while self.running:
            try:
                user_input = input(colorize("> ", 'cyan'))
                cmd, args = self.parse_command(user_input)

                if cmd:
                    self.execute_command(cmd, args)

            except KeyboardInterrupt:
                print(colorize("\n\nInterrupted. Shutting down...", 'yellow'))
                self.running = False
            except EOFError:
                self.running = False

        # Cleanup
        if self.connection and self.connection.is_open:
            self.connection.close()
        print(colorize("Guardian Agent stopped.", 'cyan'))


if __name__ == '__main__':
    guardian = GuardianLeader()
    guardian.run()

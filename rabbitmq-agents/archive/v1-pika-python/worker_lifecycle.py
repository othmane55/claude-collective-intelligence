#!/usr/bin/env python3
"""
Plugin Lifecycle Agent - Worker 1
=================================
ULTRATHINK Implementation - ETK Compliant

Role: Execute plugin lifecycle operations
- install, health, diagnose, fix, update, rollback

Auto-registers to RabbitMQ on startup.
"""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import pika
from config import (
    RABBITMQ_CONFIG, QUEUES, AGENTS, PLUGIN_MARKETPLACE_ROOT,
    MESSAGE_TYPES, colorize, print_banner
)


class PluginLifecycleWorker:
    """Plugin Lifecycle Agent - Worker for lifecycle operations."""

    def __init__(self):
        self.agent_config = AGENTS['lifecycle']
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self.running = True
        self.tasks_processed = 0

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

            # Declare and bind task queue
            self.channel.queue_declare(
                queue=QUEUES['task_queue_lifecycle'],
                durable=True
            )
            self.channel.queue_bind(
                exchange=QUEUES['task_exchange'],
                queue=QUEUES['task_queue_lifecycle'],
                routing_key='tasks.lifecycle'
            )

            # Set prefetch count (process one task at a time)
            self.channel.basic_qos(prefetch_count=1)

            print(colorize("[OK] Connected to RabbitMQ", 'green'))
            print(colorize(f"[OK] Listening on queue: {QUEUES['task_queue_lifecycle']}", 'green'))
            return True

        except pika.exceptions.AMQPConnectionError as e:
            print(colorize(f"[ERROR] Failed to connect to RabbitMQ: {e}", 'red'))
            return False

    def send_result(self, task_id: str, status: str, result: Dict[str, Any], execution_time: float):
        """Send result back to Guardian."""
        result_message = {
            'type': MESSAGE_TYPES['RESULT'],
            'task_id': task_id,
            'worker': self.agent_config['name'],
            'worker_id': self.agent_config['id'],
            'status': status,
            'result': result,
            'execution_time_ms': int(execution_time * 1000),
            'timestamp': datetime.now().isoformat(),
        }

        self.channel.basic_publish(
            exchange=QUEUES['task_exchange'],
            routing_key='results.lifecycle',
            body=json.dumps(result_message),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json',
            )
        )
        print(colorize(f"[SENT] Result for task {task_id} -> Guardian", 'green'))

    def process_task(self, task: Dict[str, Any]) -> tuple:
        """Process incoming task and return (status, result)."""
        command = task.get('command')
        params = task.get('params', {})

        print(colorize(f"\n[TASK] Received: {command}", 'yellow'))
        print(f"  Params: {params}")

        start_time = time.time()

        try:
            if command == 'health':
                result = self.check_health(params.get('plugin'))
            elif command == 'diagnose':
                result = self.diagnose_plugin(params.get('plugin'))
            elif command == 'fix':
                result = self.fix_plugin(params.get('plugin'))
            elif command == 'install':
                result = self.install_plugin(params.get('path'))
            elif command == 'update':
                result = self.update_plugin(params.get('plugin'))
            elif command == 'rollback':
                result = self.rollback_plugin(params.get('plugin'), params.get('version'))
            else:
                result = {'error': f'Unknown command: {command}'}
                return 'failed', result, time.time() - start_time

            return 'success', result, time.time() - start_time

        except Exception as e:
            return 'failed', {'error': str(e)}, time.time() - start_time

    def check_health(self, plugin_name: str) -> Dict[str, Any]:
        """Check plugin health."""
        print(colorize(f"  [EXEC] Checking health of: {plugin_name}", 'cyan'))

        plugin_path = PLUGIN_MARKETPLACE_ROOT / plugin_name

        if not plugin_path.exists():
            return {
                'plugin': plugin_name,
                'status': 'NOT_FOUND',
                'health_score': 0,
                'message': f'Plugin directory not found: {plugin_path}'
            }

        # Check structure
        checks = {
            'claude_plugin_dir': (plugin_path / '.claude-plugin').is_dir(),
            'plugin_json': (plugin_path / '.claude-plugin' / 'plugin.json').is_file(),
            'agents_dir': (plugin_path / 'agents').is_dir(),
            'skills_dir': (plugin_path / 'skills').is_dir(),
        }

        # Calculate health score
        passed = sum(checks.values())
        total = len(checks)
        health_score = int((passed / total) * 100)

        status = 'HEALTHY' if health_score >= 80 else 'WARNING' if health_score >= 50 else 'CRITICAL'

        # Count components
        agent_count = len(list((plugin_path / 'agents').glob('*.md'))) if checks['agents_dir'] else 0
        skill_count = len(list((plugin_path / 'skills').iterdir())) if checks['skills_dir'] else 0

        return {
            'plugin': plugin_name,
            'status': status,
            'health_score': health_score,
            'checks': checks,
            'components': {
                'agents': agent_count,
                'skills': skill_count,
            },
            'path': str(plugin_path),
        }

    def diagnose_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Diagnose plugin issues."""
        print(colorize(f"  [EXEC] Diagnosing: {plugin_name}", 'cyan'))

        plugin_path = PLUGIN_MARKETPLACE_ROOT / plugin_name
        issues = []
        recommendations = []

        if not plugin_path.exists():
            return {
                'plugin': plugin_name,
                'issues': ['Plugin directory not found'],
                'recommendations': ['Check plugin name spelling'],
                'error_codes': ['E404']
            }

        # E001: Check .claude-plugin structure
        claude_plugin = plugin_path / '.claude-plugin'
        if claude_plugin.is_file():
            issues.append('E001: .claude-plugin is a FILE, should be DIRECTORY')
            recommendations.append('Convert .claude-plugin file to directory')
        elif not claude_plugin.exists():
            issues.append('E002: .claude-plugin directory missing')
            recommendations.append('Create .claude-plugin/ directory with plugin.json')

        # E002: Check plugin.json location
        plugin_json_root = plugin_path / 'plugin.json'
        plugin_json_correct = plugin_path / '.claude-plugin' / 'plugin.json'

        if plugin_json_root.exists() and not plugin_json_correct.exists():
            issues.append('E002: plugin.json at root instead of .claude-plugin/')
            recommendations.append('Move plugin.json to .claude-plugin/')

        # E003: Check component placement
        for component in ['agents', 'skills', 'commands', 'hooks']:
            wrong_loc = plugin_path / '.claude-plugin' / component
            if wrong_loc.exists():
                issues.append(f'E003: {component}/ inside .claude-plugin/ (wrong location)')
                recommendations.append(f'Move {component}/ to plugin root')

        # E201: Check for shell expansion in configs
        for config_file in plugin_path.rglob('*.json'):
            try:
                content = config_file.read_text()
                if '$(' in content or '${' in content or '~/' in content:
                    issues.append(f'E201: Shell expansion in {config_file.name}')
                    recommendations.append('Replace shell expansions with absolute paths')
            except Exception:
                pass

        return {
            'plugin': plugin_name,
            'issues': issues if issues else ['No issues found'],
            'recommendations': recommendations,
            'error_codes': [i.split(':')[0] for i in issues if ':' in i],
            'issue_count': len(issues),
        }

    def fix_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Auto-fix plugin issues."""
        print(colorize(f"  [EXEC] Fixing: {plugin_name}", 'cyan'))

        # First diagnose
        diagnosis = self.diagnose_plugin(plugin_name)

        if diagnosis['issue_count'] == 0:
            return {
                'plugin': plugin_name,
                'status': 'NO_FIXES_NEEDED',
                'message': 'Plugin has no issues to fix'
            }

        # For safety, we only report what WOULD be fixed
        # Actual fixes require user confirmation (ETK compliance)
        fixes_proposed = []

        for issue in diagnosis['issues']:
            if 'E001' in issue:
                fixes_proposed.append({
                    'error': 'E001',
                    'fix': 'Convert .claude-plugin file to directory',
                    'auto_fixable': True
                })
            elif 'E002' in issue:
                fixes_proposed.append({
                    'error': 'E002',
                    'fix': 'Move plugin.json to .claude-plugin/',
                    'auto_fixable': True
                })
            elif 'E003' in issue:
                fixes_proposed.append({
                    'error': 'E003',
                    'fix': 'Move component directories to plugin root',
                    'auto_fixable': True
                })
            elif 'E201' in issue:
                fixes_proposed.append({
                    'error': 'E201',
                    'fix': 'Replace shell expansions (requires manual path input)',
                    'auto_fixable': False
                })

        return {
            'plugin': plugin_name,
            'status': 'FIXES_PROPOSED',
            'fixes': fixes_proposed,
            'message': 'Fixes proposed - confirm to apply (ETK: Ask before risky changes)',
            'requires_confirmation': True
        }

    def install_plugin(self, path: str) -> Dict[str, Any]:
        """Install plugin from path."""
        print(colorize(f"  [EXEC] Installing from: {path}", 'cyan'))

        source_path = Path(path)

        if not source_path.exists():
            return {
                'status': 'FAILED',
                'error': f'Source path not found: {path}'
            }

        # Check for plugin.json
        plugin_json = source_path / '.claude-plugin' / 'plugin.json'
        if not plugin_json.exists():
            plugin_json = source_path / 'plugin.json'

        if not plugin_json.exists():
            return {
                'status': 'FAILED',
                'error': 'No plugin.json found'
            }

        # Read plugin name
        try:
            manifest = json.loads(plugin_json.read_text())
            plugin_name = manifest.get('name', source_path.name)
        except json.JSONDecodeError:
            return {
                'status': 'FAILED',
                'error': 'Invalid plugin.json (JSON parse error)'
            }

        return {
            'status': 'READY',
            'plugin_name': plugin_name,
            'source': str(source_path),
            'message': 'Plugin validated - ready for installation',
            'requires_confirmation': True
        }

    def update_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Update plugin."""
        print(colorize(f"  [EXEC] Updating: {plugin_name}", 'cyan'))

        return {
            'plugin': plugin_name,
            'status': 'PENDING',
            'message': 'Update requires source version specification',
            'requires_confirmation': True
        }

    def rollback_plugin(self, plugin_name: str, version: str = None) -> Dict[str, Any]:
        """Rollback plugin to previous version."""
        print(colorize(f"  [EXEC] Rollback: {plugin_name} to {version}", 'cyan'))

        return {
            'plugin': plugin_name,
            'target_version': version,
            'status': 'PENDING',
            'message': 'Rollback requires backup verification',
            'requires_confirmation': True
        }

    def on_message(self, ch, method, properties, body):
        """Handle incoming message."""
        try:
            task = json.loads(body.decode())
            task_id = task.get('task_id', 'unknown')

            print(colorize(f"\n{'='*50}", 'green'))
            print(colorize(f"[RECEIVED] Task: {task_id}", 'green'))

            status, result, exec_time = self.process_task(task)

            self.send_result(task_id, status, result, exec_time)
            self.tasks_processed += 1

            print(colorize(f"[DONE] Task {task_id} completed in {exec_time:.2f}s", 'green'))
            print(colorize(f"{'='*50}\n", 'green'))

        except json.JSONDecodeError:
            print(colorize("[ERROR] Invalid JSON in message", 'red'))
        except Exception as e:
            print(colorize(f"[ERROR] Processing failed: {e}", 'red'))
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def run(self):
        """Main run loop."""
        print_banner(
            self.agent_config['name'],
            self.agent_config['role'],
            self.agent_config['color']
        )

        if not self.connect():
            return

        print(colorize("\nLifecycle Worker ready. Waiting for tasks...\n", 'green'))
        print(colorize("Capabilities:", 'yellow'))
        for cap in self.agent_config['capabilities']:
            print(f"  - {cap}")
        print()

        try:
            self.channel.basic_consume(
                queue=QUEUES['task_queue_lifecycle'],
                on_message_callback=self.on_message,
                auto_ack=False
            )
            self.channel.start_consuming()

        except KeyboardInterrupt:
            print(colorize("\n\nInterrupted. Shutting down...", 'yellow'))
            self.channel.stop_consuming()

        # Cleanup
        if self.connection and self.connection.is_open:
            self.connection.close()

        print(colorize(f"Lifecycle Worker stopped. Tasks processed: {self.tasks_processed}", 'cyan'))


if __name__ == '__main__':
    worker = PluginLifecycleWorker()
    worker.run()

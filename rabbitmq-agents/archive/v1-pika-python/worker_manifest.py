#!/usr/bin/env python3
"""
Plugin Manifest Agent - Worker 2
================================
ULTRATHINK Implementation - ETK Compliant

Role: Execute manifest validation operations
- validate_plugin, validate_manifest, check_schema, check_structure

Auto-registers to RabbitMQ on startup.
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import pika
from config import (
    RABBITMQ_CONFIG, QUEUES, AGENTS, PLUGIN_MARKETPLACE_ROOT,
    MESSAGE_TYPES, colorize, print_banner
)


class PluginManifestWorker:
    """Plugin Manifest Agent - Worker for validation operations."""

    def __init__(self):
        self.agent_config = AGENTS['manifest']
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
                queue=QUEUES['task_queue_manifest'],
                durable=True
            )
            self.channel.queue_bind(
                exchange=QUEUES['task_exchange'],
                queue=QUEUES['task_queue_manifest'],
                routing_key='tasks.manifest'
            )

            # Set prefetch count
            self.channel.basic_qos(prefetch_count=1)

            print(colorize("[OK] Connected to RabbitMQ", 'green'))
            print(colorize(f"[OK] Listening on queue: {QUEUES['task_queue_manifest']}", 'green'))
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
            routing_key='results.manifest',
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
            if command == 'validate':
                target_type = params.get('type', 'plugin')
                path = params.get('path')

                if target_type == 'plugin':
                    result = self.validate_plugin_json(path)
                elif target_type == 'manifest':
                    result = self.validate_marketplace_json(path)
                else:
                    result = self.validate_full_plugin(path)

            elif command == 'check_schema':
                result = self.check_schema(params.get('path'), params.get('schema_type'))

            elif command == 'check_structure':
                result = self.audit_structure(params.get('path'))

            elif command == 'publication_ready':
                result = self.check_publication_ready(params.get('path'))

            else:
                result = {'error': f'Unknown command: {command}'}
                return 'failed', result, time.time() - start_time

            status = 'success' if result.get('passed', False) else 'failed'
            return status, result, time.time() - start_time

        except Exception as e:
            return 'failed', {'error': str(e)}, time.time() - start_time

    def validate_plugin_json(self, path: str) -> Dict[str, Any]:
        """Validate plugin.json against official schema."""
        print(colorize(f"  [EXEC] Validating plugin.json: {path}", 'cyan'))

        issues = []
        recommendations = []

        # Resolve path
        if path.startswith('/'):
            plugin_path = Path(path)
        else:
            plugin_path = PLUGIN_MARKETPLACE_ROOT / path

        # Find plugin.json
        plugin_json = plugin_path / '.claude-plugin' / 'plugin.json'
        if not plugin_json.exists():
            plugin_json = plugin_path / 'plugin.json'

        if not plugin_json.exists():
            return {
                'passed': False,
                'path': str(plugin_path),
                'issues': ['plugin.json not found'],
                'recommendations': ['Create .claude-plugin/plugin.json']
            }

        # Check location
        if plugin_json.parent.name != '.claude-plugin':
            issues.append("LOCATION ERROR: plugin.json should be in .claude-plugin/")

        # Parse JSON
        try:
            manifest = json.loads(plugin_json.read_text())
        except json.JSONDecodeError as e:
            return {
                'passed': False,
                'path': str(plugin_json),
                'issues': [f'JSON SYNTAX ERROR: {e}'],
                'recommendations': ['Fix JSON syntax']
            }

        # Required: name
        if 'name' not in manifest:
            issues.append("MISSING REQUIRED FIELD: name")
        else:
            name = manifest['name']
            if not re.match(r'^[a-z0-9-]+$', name):
                issues.append(f"INVALID NAME: '{name}' must be kebab-case")

        # Optional but recommended
        if 'version' not in manifest:
            recommendations.append("Add 'version' field (semver: X.Y.Z)")
        else:
            version = manifest['version']
            if not re.match(r'^\d+\.\d+\.\d+$', version):
                issues.append(f"INVALID VERSION: '{version}' must be semver")

        if 'description' not in manifest:
            recommendations.append("Add 'description' field")

        if 'author' not in manifest:
            recommendations.append("Add 'author' field")

        # Check for invalid fields (E301 pattern)
        for field in ['agents', 'skills', 'commands', 'hooks']:
            if field in manifest:
                value = manifest[field]
                if isinstance(value, str) and value.startswith('./'):
                    issues.append(f"E301: '{field}' uses directory path (use file paths or delete)")

        return {
            'passed': len(issues) == 0,
            'path': str(plugin_json),
            'manifest': manifest,
            'issues': issues,
            'recommendations': recommendations,
            'validation_score': max(0, 100 - len(issues) * 20)
        }

    def validate_marketplace_json(self, path: str) -> Dict[str, Any]:
        """Validate marketplace.json against official schema."""
        print(colorize(f"  [EXEC] Validating marketplace.json: {path}", 'cyan'))

        issues = []
        recommendations = []

        # Resolve path
        if path.startswith('/'):
            marketplace_path = Path(path)
        else:
            marketplace_path = PLUGIN_MARKETPLACE_ROOT / path

        # Find marketplace.json
        if marketplace_path.is_dir():
            marketplace_json = marketplace_path / '.claude-plugin' / 'marketplace.json'
        else:
            marketplace_json = marketplace_path

        if not marketplace_json.exists():
            return {
                'passed': False,
                'path': str(marketplace_path),
                'issues': ['marketplace.json not found'],
                'recommendations': ['Create .claude-plugin/marketplace.json']
            }

        # Parse JSON
        try:
            manifest = json.loads(marketplace_json.read_text())
        except json.JSONDecodeError as e:
            return {
                'passed': False,
                'path': str(marketplace_json),
                'issues': [f'JSON SYNTAX ERROR: {e}'],
                'recommendations': ['Fix JSON syntax']
            }

        # Required: name
        if 'name' not in manifest:
            issues.append("MISSING REQUIRED FIELD: name")
        else:
            marketplace_name = manifest['name']
            if not marketplace_name.replace('-', '').isalnum():
                issues.append("INVALID NAME FORMAT: Use kebab-case")

        # Required: owner
        if 'owner' not in manifest:
            issues.append("MISSING REQUIRED FIELD: owner")
        elif 'name' not in manifest.get('owner', {}):
            issues.append("MISSING REQUIRED FIELD: owner.name")

        # Required: plugins
        if 'plugins' not in manifest:
            issues.append("MISSING REQUIRED FIELD: plugins")
        else:
            marketplace_name = manifest.get('name', '')
            for i, plugin in enumerate(manifest['plugins']):
                if 'name' not in plugin:
                    issues.append(f"PLUGIN[{i}]: Missing 'name' field")
                else:
                    # E303: Name collision check
                    if plugin['name'] == marketplace_name:
                        issues.append(
                            f"E303 NAME COLLISION: marketplace.name '{marketplace_name}' "
                            f"equals plugins[{i}].name. Rename marketplace!"
                        )

                if 'source' not in plugin:
                    issues.append(f"PLUGIN[{i}]: Missing 'source' field")
                elif not plugin['source'].startswith('./'):
                    issues.append(f"PLUGIN[{i}]: Source must start with './'")

        return {
            'passed': len(issues) == 0,
            'path': str(marketplace_json),
            'manifest': manifest,
            'issues': issues,
            'recommendations': recommendations,
            'validation_score': max(0, 100 - len(issues) * 15)
        }

    def validate_full_plugin(self, path: str) -> Dict[str, Any]:
        """Full plugin validation including structure."""
        print(colorize(f"  [EXEC] Full plugin validation: {path}", 'cyan'))

        results = {
            'plugin_json': None,
            'structure': None,
            'agents': [],
            'skills': [],
            'overall_passed': False,
            'total_issues': 0,
        }

        # Validate plugin.json
        results['plugin_json'] = self.validate_plugin_json(path)

        # Audit structure
        results['structure'] = self.audit_structure(path)

        # Validate agents
        if path.startswith('/'):
            plugin_path = Path(path)
        else:
            plugin_path = PLUGIN_MARKETPLACE_ROOT / path

        agents_dir = plugin_path / 'agents'
        if agents_dir.exists():
            for agent_file in agents_dir.glob('*.md'):
                agent_result = self.validate_agent_md(agent_file)
                results['agents'].append(agent_result)

        # Validate skills
        skills_dir = plugin_path / 'skills'
        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_md = skill_dir / 'SKILL.md'
                    if skill_md.exists():
                        skill_result = self.validate_skill_md(skill_md)
                        results['skills'].append(skill_result)

        # Calculate totals
        total_issues = len(results['plugin_json'].get('issues', []))
        total_issues += len(results['structure'].get('issues', []))
        for agent in results['agents']:
            total_issues += len(agent.get('issues', []))
        for skill in results['skills']:
            total_issues += len(skill.get('issues', []))

        results['total_issues'] = total_issues
        results['overall_passed'] = total_issues == 0

        return results

    def validate_agent_md(self, agent_path: Path) -> Dict[str, Any]:
        """Validate agent.md file."""
        issues = []

        try:
            content = agent_path.read_text()
        except Exception as e:
            return {
                'file': str(agent_path),
                'passed': False,
                'issues': [f'Read error: {e}']
            }

        # E102: Check for malformed frontmatter
        if content.startswith('>---'):
            issues.append("E102: Frontmatter starts with '>---' instead of '---'")
            return {
                'file': str(agent_path),
                'passed': False,
                'issues': issues
            }

        # Check frontmatter exists
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            issues.append("E103: Missing YAML frontmatter")
            return {
                'file': str(agent_path),
                'passed': False,
                'issues': issues
            }

        frontmatter = frontmatter_match.group(1)

        # Required fields
        if 'name:' not in frontmatter:
            issues.append("Missing required field: name")

        if 'description:' not in frontmatter:
            issues.append("Missing required field: description")

        return {
            'file': str(agent_path),
            'passed': len(issues) == 0,
            'issues': issues
        }

    def validate_skill_md(self, skill_path: Path) -> Dict[str, Any]:
        """Validate SKILL.md file."""
        issues = []

        try:
            content = skill_path.read_text()
        except Exception as e:
            return {
                'file': str(skill_path),
                'passed': False,
                'issues': [f'Read error: {e}']
            }

        # E102: Check for malformed frontmatter
        if content.startswith('>---'):
            issues.append("E102: Frontmatter starts with '>---' instead of '---'")
            return {
                'file': str(skill_path),
                'passed': False,
                'issues': issues
            }

        # Check frontmatter exists
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            issues.append("E402: Missing YAML frontmatter")
            return {
                'file': str(skill_path),
                'passed': False,
                'issues': issues
            }

        frontmatter = frontmatter_match.group(1)

        # E404: Check for nested metadata
        if frontmatter.strip().startswith('metadata:'):
            issues.append("E404: Non-standard nested 'metadata:' structure")

        # Required fields
        if 'name:' not in frontmatter:
            issues.append("Missing required field: name")

        if 'description:' not in frontmatter:
            issues.append("Missing required field: description")

        return {
            'file': str(skill_path),
            'passed': len(issues) == 0,
            'issues': issues
        }

    def audit_structure(self, path: str) -> Dict[str, Any]:
        """Audit plugin directory structure."""
        print(colorize(f"  [EXEC] Auditing structure: {path}", 'cyan'))

        issues = []
        recommendations = []

        if path.startswith('/'):
            plugin_path = Path(path)
        else:
            plugin_path = PLUGIN_MARKETPLACE_ROOT / path

        if not plugin_path.exists():
            return {
                'passed': False,
                'path': str(plugin_path),
                'issues': ['Directory not found']
            }

        # Check .claude-plugin
        claude_plugin = plugin_path / '.claude-plugin'
        if claude_plugin.is_file():
            issues.append("E001: .claude-plugin is FILE, should be DIRECTORY")
        elif not claude_plugin.exists():
            issues.append("E002: .claude-plugin/ directory missing")

        # Check plugin.json location
        if (plugin_path / 'plugin.json').exists():
            issues.append("E002: plugin.json at root (should be in .claude-plugin/)")

        # Check component placement
        for component in ['agents', 'skills', 'commands', 'hooks']:
            wrong_loc = claude_plugin / component if claude_plugin.exists() else None
            if wrong_loc and wrong_loc.exists():
                issues.append(f"E003: {component}/ inside .claude-plugin/ (move to root)")

        # Component inventory
        inventory = {
            'agents': len(list((plugin_path / 'agents').glob('*.md'))) if (plugin_path / 'agents').exists() else 0,
            'skills': len(list((plugin_path / 'skills').iterdir())) if (plugin_path / 'skills').exists() else 0,
            'commands': len(list((plugin_path / 'commands').glob('*.md'))) if (plugin_path / 'commands').exists() else 0,
        }

        return {
            'passed': len(issues) == 0,
            'path': str(plugin_path),
            'issues': issues,
            'recommendations': recommendations,
            'inventory': inventory
        }

    def check_publication_ready(self, path: str) -> Dict[str, Any]:
        """Check if plugin is ready for publication."""
        print(colorize(f"  [EXEC] Publication readiness: {path}", 'cyan'))

        # Run full validation
        full_result = self.validate_full_plugin(path)

        # Additional publication checks
        if path.startswith('/'):
            plugin_path = Path(path)
        else:
            plugin_path = PLUGIN_MARKETPLACE_ROOT / path

        publication_checks = {
            'readme_exists': (plugin_path / 'README.md').exists(),
            'no_critical_issues': full_result['total_issues'] == 0,
            'has_agents_or_skills': (
                len(full_result.get('agents', [])) > 0 or
                len(full_result.get('skills', [])) > 0
            ),
        }

        ready = all(publication_checks.values())

        return {
            'passed': ready,
            'publication_ready': ready,
            'checks': publication_checks,
            'total_issues': full_result['total_issues'],
            'verdict': 'READY FOR PUBLICATION' if ready else 'NOT READY',
        }

    def on_message(self, ch, method, properties, body):
        """Handle incoming message."""
        try:
            task = json.loads(body.decode())
            task_id = task.get('task_id', 'unknown')

            print(colorize(f"\n{'='*50}", 'yellow'))
            print(colorize(f"[RECEIVED] Task: {task_id}", 'yellow'))

            status, result, exec_time = self.process_task(task)

            self.send_result(task_id, status, result, exec_time)
            self.tasks_processed += 1

            print(colorize(f"[DONE] Task {task_id} completed in {exec_time:.2f}s", 'green'))
            print(colorize(f"{'='*50}\n", 'yellow'))

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

        print(colorize("\nManifest Worker ready. Waiting for tasks...\n", 'green'))
        print(colorize("Capabilities:", 'yellow'))
        for cap in self.agent_config['capabilities']:
            print(f"  - {cap}")
        print()

        try:
            self.channel.basic_consume(
                queue=QUEUES['task_queue_manifest'],
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

        print(colorize(f"Manifest Worker stopped. Tasks processed: {self.tasks_processed}", 'cyan'))


if __name__ == '__main__':
    worker = PluginManifestWorker()
    worker.run()

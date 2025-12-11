#!/usr/bin/env python3
"""
RabbitMQ Multi-Agent System Configuration
==========================================
ULTRATHINK Implementation - ETK Compliant

Team:
- Guardian Agent (Team Leader)
- Plugin Lifecycle Agent (Worker 1)
- Plugin Manifest Agent (Worker 2)
"""

import os
from pathlib import Path

# RabbitMQ Connection Configuration (Docker: agent_rabbitmq)
RABBITMQ_CONFIG = {
    'host': os.getenv('RABBITMQ_HOST', 'localhost'),
    'port': int(os.getenv('RABBITMQ_PORT', 5672)),
    'virtual_host': '/',
    'credentials': {
        'username': os.getenv('RABBITMQ_USER', 'admin'),
        'password': os.getenv('RABBITMQ_PASS', 'rabbitmq123'),
    }
}

# Queue Configuration
QUEUES = {
    'task_exchange': 'agent_exchange',
    'task_queue_lifecycle': 'tasks.lifecycle',
    'task_queue_manifest': 'tasks.manifest',
    'result_queue': 'results.guardian',
    'broadcast_queue': 'broadcast.all',
}

# Agent Definitions
AGENTS = {
    'guardian': {
        'id': 'guardian-001',
        'name': 'Guardian Agent',
        'role': 'Team Leader',
        'color': 'cyan',
        'source_file': '/Users/umitkacar/Documents/claude-plugins-marketplace/fingerphoto-aqis-lite/agents/guardian-agent.md',
        'capabilities': [
            'validate',           # Validate worker results
            'distribute',         # Distribute tasks to workers
            'monitor',            # Monitor system health
            'skeptical_review',   # Challenge all claims
        ],
        'routing_keys': ['tasks.*', 'results.*'],
    },
    'lifecycle': {
        'id': 'lifecycle-001',
        'name': 'Plugin Lifecycle Agent',
        'role': 'Worker',
        'color': 'green',
        'source_file': '/Users/umitkacar/Documents/claude-plugins-marketplace/claude-hooks-orchestrator/agents/plugin-lifecycle-agent.md',
        'capabilities': [
            'install',            # Plugin installation
            'health',             # Health monitoring
            'diagnose',           # Problem diagnosis
            'fix',                # Auto-fix issues
            'update',             # Plugin updates
            'rollback',           # Version rollback
        ],
        'routing_key': 'tasks.lifecycle',
    },
    'manifest': {
        'id': 'manifest-001',
        'name': 'Plugin Manifest Agent',
        'role': 'Worker',
        'color': 'yellow',
        'source_file': '/Users/umitkacar/Documents/claude-plugins-marketplace/claude-hooks-orchestrator/agents/plugin-manifest-agent.md',
        'capabilities': [
            'validate_plugin',    # Validate plugin.json
            'validate_manifest',  # Validate marketplace.json
            'check_schema',       # Schema validation
            'check_structure',    # Directory structure audit
            'publication_ready',  # Publication readiness check
        ],
        'routing_key': 'tasks.manifest',
    }
}

# Command Routing Map (which worker handles which command)
COMMAND_ROUTING = {
    # Plugin Lifecycle Agent commands
    'install': 'lifecycle',
    'health': 'lifecycle',
    'diagnose': 'lifecycle',
    'fix': 'lifecycle',
    'update': 'lifecycle',
    'rollback': 'lifecycle',

    # Plugin Manifest Agent commands
    'validate': 'manifest',
    'check': 'manifest',
    'schema': 'manifest',
    'structure': 'manifest',
    'publish': 'manifest',
}

# Message Types
MESSAGE_TYPES = {
    'TASK': 'task',
    'RESULT': 'result',
    'HEARTBEAT': 'heartbeat',
    'REGISTER': 'register',
    'BROADCAST': 'broadcast',
}

# Paths
PLUGIN_MARKETPLACE_ROOT = Path('/Users/umitkacar/Documents/claude-plugins-marketplace')
PLUGINS = [
    'fingerphoto-aqis-lite',
    'claude-hooks-orchestrator',
    'fingerphoto-train-eval-vis',
    'claude-collective-orchestrator',
    'claude-external-intelligence',
    'claude-github-orchestrator',
]

# Terminal Colors (ANSI)
COLORS = {
    'reset': '\033[0m',
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'bold': '\033[1m',
}

def colorize(text: str, color: str) -> str:
    """Apply color to text for terminal output."""
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"

def print_banner(agent_name: str, role: str, color: str):
    """Print agent startup banner."""
    banner = f"""
{colorize('='*60, color)}
{colorize(f'  {agent_name}', 'bold')}
{colorize(f'  Role: {role}', color)}
{colorize(f'  RabbitMQ: {RABBITMQ_CONFIG["host"]}:{RABBITMQ_CONFIG["port"]}', color)}
{colorize('='*60, color)}
"""
    print(banner)

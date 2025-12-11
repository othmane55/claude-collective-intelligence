#!/usr/bin/env python3
"""
Demo 1 Configuration - Role Assignment
"""

# RabbitMQ Connection
RABBITMQ_CONFIG = {
    'host': 'localhost',
    'port': 5672,
    'virtual_host': '/',
    'credentials': {
        'username': 'admin',
        'password': 'rabbitmq123'
    }
}

# Queue Names
QUEUES = {
    'role_assignments': 'role.assignments',
    'role_acknowledgments': 'role.acknowledgments'
}

# Colors for terminal output
COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'bold': '\033[1m',
    'reset': '\033[0m'
}

def colorize(text: str, color: str) -> str:
    """Add color to text."""
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"

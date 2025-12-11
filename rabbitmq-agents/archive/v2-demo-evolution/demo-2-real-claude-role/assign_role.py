#!/usr/bin/env python3 -u
"""
Assign Role - Main Claude's Tool
================================
Sends role assignment to Sub-Claude via RabbitMQ.

Usage:
    python3 assign_role.py "Team Leader" "guardian"
"""

import sys
import os
import json
from datetime import datetime

os.environ['PYTHONUNBUFFERED'] = '1'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

import pika
from config import RABBITMQ_CONFIG, QUEUES, colorize


def assign_role(role: str, agent_name: str) -> dict:
    """Send role assignment to Sub-Claude."""

    print(colorize("\n" + "="*60, 'magenta'), flush=True)
    print(colorize("  MAIN CLAUDE: ASSIGNING ROLE", 'bold'), flush=True)
    print(colorize("="*60, 'magenta'), flush=True)

    try:
        credentials = pika.PlainCredentials(
            RABBITMQ_CONFIG['credentials']['username'],
            RABBITMQ_CONFIG['credentials']['password']
        )
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_CONFIG['host'],
            port=RABBITMQ_CONFIG['port'],
            virtual_host=RABBITMQ_CONFIG['virtual_host'],
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Declare queues
        channel.queue_declare(queue=QUEUES['role_assignments'], durable=True)
        channel.queue_declare(queue=QUEUES['role_acknowledgments'], durable=True)

        # Purge ack queue for fresh response
        channel.queue_purge(queue=QUEUES['role_acknowledgments'])

        # Create message
        message = {
            'role': role,
            'agent': agent_name,
            'timestamp': datetime.now().isoformat(),
            'assigned_by': 'main_claude'
        }

        print(colorize(f"  Role:   {role}", 'cyan'), flush=True)
        print(colorize(f"  Agent:  {agent_name}", 'white'), flush=True)
        print(colorize("="*60 + "\n", 'magenta'), flush=True)

        # Send
        channel.basic_publish(
            exchange='',
            routing_key=QUEUES['role_assignments'],
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        print(colorize("[SENT] Role assignment sent!", 'green'), flush=True)
        print(colorize("[WAIT] Waiting for acknowledgment...\n", 'yellow'), flush=True)

        # Wait for ack
        import time
        start = time.time()
        while time.time() - start < 30:
            method, props, body = channel.basic_get(
                queue=QUEUES['role_acknowledgments'],
                auto_ack=True
            )
            if body:
                ack = json.loads(body.decode())
                print(colorize("\n" + "="*60, 'green'), flush=True)
                print(colorize("  ACKNOWLEDGMENT RECEIVED!", 'bold'), flush=True)
                print(colorize("="*60, 'green'), flush=True)
                print(colorize(f"  From:    {ack.get('agent')}", 'white'), flush=True)
                print(colorize(f"  Status:  {ack.get('status')}", 'cyan'), flush=True)
                print(colorize(f"  Message: {ack.get('message')}", 'white'), flush=True)
                print(colorize("="*60 + "\n", 'green'), flush=True)
                connection.close()
                return {'success': True, 'ack': ack}
            time.sleep(0.5)

        connection.close()
        print(colorize("[TIMEOUT] No acknowledgment received", 'red'), flush=True)
        return {'success': False, 'error': 'timeout'}

    except Exception as e:
        print(colorize(f"[ERROR] {e}", 'red'), flush=True)
        return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    role = sys.argv[1] if len(sys.argv) > 1 else "Worker"
    agent = sys.argv[2] if len(sys.argv) > 2 else "sub-claude"
    result = assign_role(role, agent)
    print(f"\n[RESULT] {json.dumps(result, indent=2)}")

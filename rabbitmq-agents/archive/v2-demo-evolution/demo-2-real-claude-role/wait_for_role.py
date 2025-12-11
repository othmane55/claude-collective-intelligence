#!/usr/bin/env python3 -u
"""
Wait For Role - Sub-Claude's First Task
=======================================
This script is run by Sub-Claude to wait for role assignment from Main Claude.

Usage (by Sub-Claude):
    python3 wait_for_role.py

Returns:
    JSON with role information when received
"""

import sys
import os
import json
from datetime import datetime

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

import pika
from config import RABBITMQ_CONFIG, QUEUES, colorize


def wait_for_role(timeout: int = 60) -> dict:
    """Wait for role assignment from Main Claude."""

    print(colorize("\n" + "="*60, 'cyan'), flush=True)
    print(colorize("  SUB-CLAUDE: WAITING FOR ROLE ASSIGNMENT", 'bold'), flush=True)
    print(colorize("="*60, 'cyan'), flush=True)
    print(colorize(f"  Queue: {QUEUES['role_assignments']}", 'white'), flush=True)
    print(colorize(f"  Timeout: {timeout} seconds", 'white'), flush=True)
    print(colorize("="*60 + "\n", 'cyan'), flush=True)

    try:
        # Connect to RabbitMQ
        credentials = pika.PlainCredentials(
            RABBITMQ_CONFIG['credentials']['username'],
            RABBITMQ_CONFIG['credentials']['password']
        )
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_CONFIG['host'],
            port=RABBITMQ_CONFIG['port'],
            virtual_host=RABBITMQ_CONFIG['virtual_host'],
            credentials=credentials,
            heartbeat=30
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Declare queues
        channel.queue_declare(queue=QUEUES['role_assignments'], durable=True)
        channel.queue_declare(queue=QUEUES['role_acknowledgments'], durable=True)

        print(colorize("[OK] Connected to RabbitMQ", 'green'), flush=True)
        print(colorize("[WAIT] Listening for role assignment...\n", 'yellow'), flush=True)

        # Wait for message with timeout
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            method, properties, body = channel.basic_get(
                queue=QUEUES['role_assignments'],
                auto_ack=False
            )

            if body:
                message = json.loads(body.decode())
                role = message.get('role', 'Unknown')
                assigned_by = message.get('assigned_by', 'Unknown')
                agent_name = message.get('agent', 'sub-claude')

                # Print role received
                print(colorize("\n" + "="*60, 'green'), flush=True)
                print(colorize("  ROLE RECEIVED!", 'bold'), flush=True)
                print(colorize("="*60, 'green'), flush=True)
                print(colorize(f"  Role:        {role}", 'cyan'), flush=True)
                print(colorize(f"  Agent:       {agent_name}", 'white'), flush=True)
                print(colorize(f"  Assigned by: {assigned_by}", 'white'), flush=True)
                print(colorize("="*60, 'green'), flush=True)
                print(colorize("  STATUS: ROLE ACCEPTED!", 'green'), flush=True)
                print(colorize("="*60 + "\n", 'green'), flush=True)

                # Acknowledge to RabbitMQ
                channel.basic_ack(delivery_tag=method.delivery_tag)

                # Send acknowledgment to Main Claude
                ack_message = {
                    'status': 'accepted',
                    'agent': agent_name,
                    'role': role,
                    'message': f'Sub-Claude accepted role: {role}',
                    'timestamp': datetime.now().isoformat(),
                    'instance': 'sub-claude'
                }

                channel.basic_publish(
                    exchange='',
                    routing_key=QUEUES['role_acknowledgments'],
                    body=json.dumps(ack_message),
                    properties=pika.BasicProperties(delivery_mode=2)
                )

                print(colorize("[SENT] Acknowledgment sent to Main Claude", 'blue'), flush=True)

                connection.close()

                # Return role info as JSON for Claude to use
                return {
                    'success': True,
                    'role': role,
                    'agent': agent_name,
                    'assigned_by': assigned_by
                }

            time.sleep(0.5)

        # Timeout
        connection.close()
        print(colorize("\n[TIMEOUT] No role received within timeout period", 'red'), flush=True)
        return {'success': False, 'error': 'timeout'}

    except Exception as e:
        print(colorize(f"\n[ERROR] {e}", 'red'), flush=True)
        return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    result = wait_for_role(timeout=60)
    print(f"\n[RESULT] {json.dumps(result, indent=2)}", flush=True)

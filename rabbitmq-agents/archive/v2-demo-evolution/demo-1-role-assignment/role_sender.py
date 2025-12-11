#!/usr/bin/env python3 -u
"""
Role Sender - Main Claude's Tool
================================
Sends role assignments to agents via RabbitMQ.
Waits for and displays acknowledgment.

Usage:
    python3 role_sender.py --role "Role Name" --agent "agent_name"

Example:
    python3 role_sender.py --role "Team Leader" --agent "guardian"
"""

import sys
import os
import json
import argparse
from datetime import datetime

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

import pika
from config import RABBITMQ_CONFIG, QUEUES, colorize


class RoleSender:
    def __init__(self):
        self.connection = None
        self.channel = None

    def connect(self):
        """Connect to RabbitMQ."""
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
                heartbeat=30
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare queues
            self.channel.queue_declare(queue=QUEUES['role_assignments'], durable=True)
            self.channel.queue_declare(queue=QUEUES['role_acknowledgments'], durable=True)

            # Purge acknowledgment queue to get fresh responses
            self.channel.queue_purge(queue=QUEUES['role_acknowledgments'])

            return True
        except Exception as e:
            print(colorize(f"[ERROR] Connection failed: {e}", 'red'), flush=True)
            return False

    def send_role(self, role: str, agent: str) -> dict:
        """Send role assignment and wait for acknowledgment."""
        if not self.connect():
            return None

        # Create role assignment message
        message = {
            'role': role,
            'agent': agent,
            'timestamp': datetime.now().isoformat(),
            'assigned_by': 'main_claude'
        }

        print(colorize(f"\n{'='*60}", 'magenta'), flush=True)
        print(colorize(f"  SENDING ROLE ASSIGNMENT", 'bold'), flush=True)
        print(colorize(f"{'='*60}", 'magenta'), flush=True)
        print(colorize(f"  Target Agent: {agent}", 'white'), flush=True)
        print(colorize(f"  Role:         {role}", 'cyan'), flush=True)
        print(colorize(f"  Timestamp:    {message['timestamp']}", 'white'), flush=True)
        print(colorize(f"{'='*60}\n", 'magenta'), flush=True)

        # Send the role assignment
        self.channel.basic_publish(
            exchange='',
            routing_key=QUEUES['role_assignments'],
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        print(colorize(f"[SENT] Role assignment sent to queue", 'green'), flush=True)
        print(colorize(f"[WAIT] Waiting for acknowledgment...\n", 'yellow'), flush=True)

        # Wait for acknowledgment (with timeout)
        ack = self.wait_for_ack(agent, timeout=10)

        if ack:
            print(colorize(f"\n{'='*60}", 'green'), flush=True)
            print(colorize(f"  ACKNOWLEDGMENT RECEIVED!", 'bold'), flush=True)
            print(colorize(f"{'='*60}", 'green'), flush=True)
            print(colorize(f"  From Agent:  {ack.get('agent', 'Unknown')}", 'white'), flush=True)
            print(colorize(f"  Status:      {ack.get('status', 'Unknown')}", 'cyan'), flush=True)
            print(colorize(f"  Message:     {ack.get('message', '')}", 'white'), flush=True)
            print(colorize(f"  Timestamp:   {ack.get('timestamp', '')}", 'white'), flush=True)
            print(colorize(f"{'='*60}\n", 'green'), flush=True)
        else:
            print(colorize(f"\n[TIMEOUT] No acknowledgment received within 10 seconds", 'red'), flush=True)
            print(colorize(f"[HINT] Make sure the agent is running!", 'yellow'), flush=True)

        self.connection.close()
        return ack

    def wait_for_ack(self, expected_agent: str, timeout: int = 10) -> dict:
        """Wait for acknowledgment from specific agent."""
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            method, properties, body = self.channel.basic_get(
                queue=QUEUES['role_acknowledgments'],
                auto_ack=True
            )

            if body:
                try:
                    ack = json.loads(body.decode())
                    if ack.get('agent') == expected_agent:
                        return ack
                except json.JSONDecodeError:
                    continue

            time.sleep(0.1)

        return None


def main():
    parser = argparse.ArgumentParser(description='Send role assignment to agent')
    parser.add_argument('--role', '-r', required=True, help='Role to assign')
    parser.add_argument('--agent', '-a', required=True, help='Target agent name')

    args = parser.parse_args()

    sender = RoleSender()
    result = sender.send_role(args.role, args.agent)

    # Exit with appropriate code
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()

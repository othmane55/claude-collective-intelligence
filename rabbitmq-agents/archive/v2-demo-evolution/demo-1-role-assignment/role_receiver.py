#!/usr/bin/env python3 -u
"""
Role Receiver Agent
===================
Listens for role assignments from Main Claude via RabbitMQ.
Acknowledges role receipt back to Main Claude.

Usage:
    python3 role_receiver.py [agent_name]

Example:
    python3 role_receiver.py guardian
"""

import sys
import os
import json
import signal
from datetime import datetime

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

import pika
from config import RABBITMQ_CONFIG, QUEUES, colorize

class RoleReceiver:
    def __init__(self, agent_name: str = "agent"):
        self.agent_name = agent_name
        self.current_role = None
        self.running = True
        self.connection = None
        self.channel = None

        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        print(colorize(f"\n[{self.agent_name}] Shutting down...", 'yellow'), flush=True)
        self.running = False
        if self.connection and self.connection.is_open:
            self.connection.close()
        sys.exit(0)

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

            print(colorize(f"[{self.agent_name}] Connected to RabbitMQ", 'green'), flush=True)
            return True
        except Exception as e:
            print(colorize(f"[{self.agent_name}] Connection failed: {e}", 'red'), flush=True)
            return False

    def process_role(self, ch, method, properties, body):
        """Process incoming role assignment."""
        try:
            message = json.loads(body.decode())

            # Check if this message is for us
            target_agent = message.get('agent', '')
            if target_agent and target_agent != self.agent_name:
                # Not for us, reject and requeue
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return

            role = message.get('role', 'Unknown')
            assigned_by = message.get('assigned_by', 'Unknown')
            timestamp = message.get('timestamp', '')

            # Accept the role
            self.current_role = role

            # Print role acceptance
            print(colorize(f"\n{'='*60}", 'cyan'), flush=True)
            print(colorize(f"  ROLE ASSIGNMENT RECEIVED", 'bold'), flush=True)
            print(colorize(f"{'='*60}", 'cyan'), flush=True)
            print(colorize(f"  Agent:       {self.agent_name}", 'white'), flush=True)
            print(colorize(f"  Role:        {role}", 'green'), flush=True)
            print(colorize(f"  Assigned by: {assigned_by}", 'white'), flush=True)
            print(colorize(f"  Timestamp:   {timestamp}", 'white'), flush=True)
            print(colorize(f"{'='*60}", 'cyan'), flush=True)
            print(colorize(f"  STATUS: ROLE ACCEPTED AND ACTIVATED!", 'green'), flush=True)
            print(colorize(f"{'='*60}\n", 'cyan'), flush=True)

            # Send acknowledgment
            ack_message = {
                'status': 'accepted',
                'agent': self.agent_name,
                'role': role,
                'message': f'{self.agent_name} accepted role: {role}',
                'timestamp': datetime.now().isoformat()
            }

            self.channel.basic_publish(
                exchange='',
                routing_key=QUEUES['role_acknowledgments'],
                body=json.dumps(ack_message),
                properties=pika.BasicProperties(delivery_mode=2)
            )

            print(colorize(f"[{self.agent_name}] Acknowledgment sent to Main Claude", 'blue'), flush=True)

            # Acknowledge message processing
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(colorize(f"[{self.agent_name}] Error processing role: {e}", 'red'), flush=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def run(self):
        """Start listening for role assignments."""
        if not self.connect():
            return

        # Print startup banner
        print(colorize(f"""
╔══════════════════════════════════════════════════════════╗
║  ROLE RECEIVER AGENT                                     ║
║  Agent Name: {self.agent_name:<43} ║
║  Status: WAITING FOR ROLE ASSIGNMENT                     ║
╚══════════════════════════════════════════════════════════╝
""", 'cyan'), flush=True)

        print(colorize(f"[{self.agent_name}] Listening on queue: {QUEUES['role_assignments']}", 'white'), flush=True)
        print(colorize(f"[{self.agent_name}] Press Ctrl+C to exit\n", 'white'), flush=True)

        # Start consuming
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=QUEUES['role_assignments'],
            on_message_callback=self.process_role
        )

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self._shutdown(None, None)


def main():
    agent_name = sys.argv[1] if len(sys.argv) > 1 else "agent"
    receiver = RoleReceiver(agent_name)
    receiver.run()


if __name__ == '__main__':
    main()

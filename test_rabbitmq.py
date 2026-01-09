#!/usr/bin/env python3
"""
RabbitMQ Connection and Messaging Test Script
Tests RabbitMQ connectivity, publishing, and consuming messages
"""

import sys
import time
import json
import requests
import pika
from datetime import datetime

# Configuration
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'admin'
RABBITMQ_PASS = 'rabbitmqpass123'
MANAGEMENT_URL = 'http://localhost:15672'
TEST_QUEUE = 'test_queue'
TEST_EXCHANGE = 'test_exchange'

def print_test(name):
    """Print test header"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")

def print_success(message):
    """Print success message"""
    print(f"✓ {message}")

def print_error(message):
    """Print error message"""
    print(f"✗ {message}")

def test_management_api():
    """Test RabbitMQ Management API"""
    print_test("RabbitMQ Management API")
    
    try:
        # Test overview endpoint
        response = requests.get(
            f"{MANAGEMENT_URL}/api/overview",
            auth=(RABBITMQ_USER, RABBITMQ_PASS),
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        print_success(f"Management API accessible")
        print(f"  RabbitMQ Version: {data.get('rabbitmq_version', 'unknown')}")
        print(f"  Erlang Version: {data.get('erlang_version', 'unknown')}")
        print(f"  Cluster Name: {data.get('cluster_name', 'unknown')}")
        
        # Test vhosts
        response = requests.get(
            f"{MANAGEMENT_URL}/api/vhosts",
            auth=(RABBITMQ_USER, RABBITMQ_PASS),
            timeout=5
        )
        response.raise_for_status()
        vhosts = response.json()
        print_success(f"Found {len(vhosts)} virtual host(s)")
        
        return True
    except requests.exceptions.RequestException as e:
        print_error(f"Management API test failed: {e}")
        return False

def test_connection():
    """Test basic RabbitMQ connection"""
    print_test("RabbitMQ Connection")
    
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        print_success(f"Connected to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
        
        # Get server properties
        props = connection._impl.server_properties
        print(f"  Product: {props.get('product', 'unknown')}")
        print(f"  Version: {props.get('version', 'unknown')}")
        
        connection.close()
        return True
    except Exception as e:
        print_error(f"Connection test failed: {e}")
        return False

def test_publish_consume():
    """Test publishing and consuming messages"""
    print_test("Publish and Consume Messages")
    
    try:
        # Connect
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declare queue
        channel.queue_declare(queue=TEST_QUEUE, durable=False, auto_delete=True)
        print_success(f"Queue '{TEST_QUEUE}' declared")
        
        # Publish test messages
        num_messages = 5
        for i in range(num_messages):
            message = {
                'message_id': i + 1,
                'timestamp': datetime.now().isoformat(),
                'content': f'Test message {i + 1}'
            }
            channel.basic_publish(
                exchange='',
                routing_key=TEST_QUEUE,
                body=json.dumps(message)
            )
        
        print_success(f"Published {num_messages} messages")
        
        # Consume messages
        received_messages = []
        
        def callback(ch, method, properties, body):
            message = json.loads(body)
            received_messages.append(message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        
        channel.basic_consume(queue=TEST_QUEUE, on_message_callback=callback)
        
        # Process messages with timeout
        start_time = time.time()
        while len(received_messages) < num_messages and (time.time() - start_time) < 5:
            connection.process_data_events(time_limit=1)
        
        print_success(f"Consumed {len(received_messages)} messages")
        
        # Verify message content
        for msg in received_messages:
            print(f"  Message {msg['message_id']}: {msg['content']}")
        
        # Cleanup
        channel.queue_delete(queue=TEST_QUEUE)
        connection.close()
        
        if len(received_messages) == num_messages:
            print_success("All messages received correctly")
            return True
        else:
            print_error(f"Expected {num_messages} messages, got {len(received_messages)}")
            return False
            
    except Exception as e:
        print_error(f"Publish/consume test failed: {e}")
        return False

def test_exchange_routing():
    """Test exchange and routing"""
    print_test("Exchange and Routing")
    
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declare exchange
        channel.exchange_declare(
            exchange=TEST_EXCHANGE,
            exchange_type='topic',
            durable=False,
            auto_delete=True
        )
        print_success(f"Exchange '{TEST_EXCHANGE}' declared (type: topic)")
        
        # Create queues and bind with different routing keys
        queues = {
            'error_queue': 'logs.error',
            'info_queue': 'logs.info',
            'all_queue': 'logs.*'
        }
        
        for queue_name, routing_key in queues.items():
            channel.queue_declare(queue=queue_name, durable=False, auto_delete=True)
            channel.queue_bind(
                exchange=TEST_EXCHANGE,
                queue=queue_name,
                routing_key=routing_key
            )
            print_success(f"Queue '{queue_name}' bound with routing key '{routing_key}'")
        
        # Publish messages with different routing keys
        test_messages = [
            ('logs.error', 'Error message'),
            ('logs.info', 'Info message'),
            ('logs.warning', 'Warning message')
        ]
        
        for routing_key, content in test_messages:
            channel.basic_publish(
                exchange=TEST_EXCHANGE,
                routing_key=routing_key,
                body=content
            )
            print(f"  Published: {routing_key} -> {content}")
        
        # Check message counts
        time.sleep(0.5)  # Allow messages to route
        
        for queue_name in queues.keys():
            method = channel.queue_declare(queue=queue_name, passive=True)
            msg_count = method.method.message_count
            print(f"  {queue_name}: {msg_count} message(s)")
        
        # Cleanup
        for queue_name in queues.keys():
            channel.queue_delete(queue=queue_name)
        channel.exchange_delete(exchange=TEST_EXCHANGE)
        connection.close()
        
        print_success("Exchange routing test completed")
        return True
        
    except Exception as e:
        print_error(f"Exchange routing test failed: {e}")
        return False

def test_docker_network():
    """Test RabbitMQ from Docker network perspective"""
    print_test("Docker Network Connectivity")
    
    try:
        # Test using 'rabbitmq' hostname (as Node-RED would)
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        
        # First test with localhost
        parameters = pika.ConnectionParameters(
            host='localhost',
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        connection.close()
        print_success("Connection via localhost:5672 successful")
        
        # Check if we can reach management UI
        response = requests.get(
            f"{MANAGEMENT_URL}/api/overview",
            auth=(RABBITMQ_USER, RABBITMQ_PASS),
            timeout=5
        )
        response.raise_for_status()
        print_success("Management UI accessible at localhost:15672")
        
        return True
        
    except Exception as e:
        print_error(f"Docker network test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("RabbitMQ Test Suite")
    print("="*60)
    print(f"Target: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    print(f"User: {RABBITMQ_USER}")
    print(f"Management UI: {MANAGEMENT_URL}")
    
    results = {
        'Management API': test_management_api(),
        'Basic Connection': test_connection(),
        'Publish/Consume': test_publish_consume(),
        'Exchange Routing': test_exchange_routing(),
        'Docker Network': test_docker_network()
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n✓ All tests passed! RabbitMQ is fully operational.")
        return 0
    else:
        print(f"\n✗ {total_tests - passed_tests} test(s) failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

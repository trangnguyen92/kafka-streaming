# sample_producer.py
# Sample producer to test the ETL pipeline

import json
import time
import uuid
from datetime import datetime
from confluent_kafka import Producer


def delivery_report(err, msg):
    """Delivery report callback"""
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')


def create_sample_event(event_type: str = "user_action"):
    """Create a sample event for testing"""
    return {
        'id': str(uuid.uuid4()),
        'event_type': event_type,
        'user_id': f'user_{uuid.uuid4().hex[:8]}',
        'timestamp': datetime.utcnow().isoformat(),
        'data': {
            'action': 'click',
            'page': '/dashboard',
            'session_id': str(uuid.uuid4()),
            'user_agent': 'Mozilla/5.0 (Test Browser)',
            'ip_address': '192.168.1.100'
        }
    }


def main():
    # Kafka producer configuration
    producer_config = {
        'bootstrap.servers': 'localhost:9092',
        'client.id': 'sample_producer'
    }

    producer = Producer(producer_config)
    topic = 'data_events'

    print("Starting sample producer...")
    print("Press Ctrl+C to stop")

    try:
        while True:
            # Create sample events
            events = [
                create_sample_event('user_login'),
                create_sample_event('page_view'),
                create_sample_event('user_action'),
                create_sample_event('purchase'),
            ]

            for event in events:
                # Send event to Kafka
                producer.produce(
                    topic=topic,
                    key=event['id'],
                    value=json.dumps(event),
                    callback=delivery_report
                )

                print(f"Sent event: {event['event_type']} - {event['id']}")

            # Wait for any outstanding messages to be delivered
            producer.flush()

            # Wait before sending next batch
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nStopping producer...")
    finally:
        producer.flush()
        print("Producer stopped")


if __name__ == "__main__":
    main()
# etl-service/consumer.py
import json
import logging
import os
import time
from typing import Dict, Any
from datetime import datetime

from confluent_kafka import Consumer, KafkaError
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETLProcessor:
    def __init__(self):
        self.kafka_config = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            'group.id': os.getenv('KAFKA_GROUP_ID', 'etl_consumer_group'),
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
            'max.poll.interval.ms': 300000,
        }

        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'etl_db'),
            'user': os.getenv('DB_USER', 'etl_user'),
            'password': os.getenv('DB_PASSWORD', 'etl_password')
        }

        self.topic = os.getenv('KAFKA_TOPIC', 'data_events')

        # Initialize connections
        self.consumer = None
        self.db_engine = None
        self.init_connections()

    def init_connections(self):
        """Initialize Kafka consumer and database connection"""
        try:
            # Initialize Kafka consumer
            self.consumer = Consumer(self.kafka_config)
            self.consumer.subscribe([self.topic])
            logger.info(f"Subscribed to Kafka topic: {self.topic}")

            # Initialize database connection
            db_url = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            self.db_engine = create_engine(db_url)
            logger.info("Database connection established")

        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}")
            raise

    def process_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and transform the message data
        Add your business logic here
        """
        try:
            processed_data = {
                'id': message_data.get('id'),
                'event_type': message_data.get('event_type', 'unknown'),
                'user_id': message_data.get('user_id'),
                'timestamp': message_data.get('timestamp', datetime.utcnow().isoformat()),
                'data': json.dumps(message_data.get('data', {})),
                'processed_at': datetime.utcnow().isoformat()
            }

            # Add any additional processing logic here
            logger.info(f"Processed message: {processed_data.get('id', 'unknown')}")
            return processed_data

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise

    def save_to_database(self, processed_data: Dict[str, Any]):
        """Save processed data to PostgreSQL database"""
        try:
            with self.db_engine.connect() as conn:
                # Insert into events table
                insert_query = text("""
                                    INSERT INTO events (id, event_type, user_id, timestamp, data, processed_at)
                                    VALUES (:id, :event_type, :user_id, :timestamp, :data, :processed_at)
                                    ON CONFLICT
                                        (id)
                                        DO UPDATE SET
                        event_type = EXCLUDED.event_type,
                        user_id = EXCLUDED.user_id,
                        timestamp = EXCLUDED.timestamp,
                        data = EXCLUDED.data,
                        processed_at = EXCLUDED.processed_at
                                    """)

                conn.execute(insert_query, processed_data)
                conn.commit()
                logger.info(f"Saved record to database: {processed_data.get('id', 'unknown')}")

        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            raise

    def run(self):
        """Main ETL processing loop"""
        logger.info("Starting ETL consumer...")

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"End of partition reached {msg.topic()}/{msg.partition()}")
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                    continue

                try:
                    # Decode message
                    message_data = json.loads(msg.value().decode('utf-8'))
                    logger.info(f"Received message: {message_data}")

                    # Process message
                    processed_data = self.process_message(message_data)

                    # Save to database
                    self.save_to_database(processed_data)

                    # Commit offset
                    self.consumer.commit(msg)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue

        except KeyboardInterrupt:
            logger.info("Stopping ETL consumer...")
        finally:
            if self.consumer:
                self.consumer.close()
            logger.info("ETL consumer stopped")


if __name__ == "__main__":
    # Wait for dependencies to be ready
    time.sleep(10)

    processor = ETLProcessor()
    processor.run()

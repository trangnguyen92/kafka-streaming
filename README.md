# ETL Kafka-Streaming Stack Setup

This Docker Compose stack provides a complete ETL pipeline with Kafka and PostgreSQL for processing streaming data.

## Architecture

- **Kafka**: Message broker for streaming data
- **Zookeeper**: Kafka coordination service
- **PostgreSQL**: Database for storing processed data
- **ETL Consumer**: Python service using confluent-kafka to process messages
- **Kafka UI**: Web interface for monitoring Kafka (optional)
- **Sample Producer**: Python script to produce test messages to Kafka


## Directory Structure

```
kafka-streaming/
.
├── docker-compose.yml
├── etl-service
│   ├── consumer.py
│   ├── Dockerfile
│   └── requirements.txt
├── init-db.sql
├── README.md
└── test_producer.py

2 directories, 7 files

```

## Quick Start

1. **Start the stack:**
   ```bash
   docker-compose up -d
   ```

2. **Check if services are running:**
   ```bash
   docker-compose ps
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f etl-consumer
   ```

## Testing the Pipeline

1. **Install required python packages locally** (for the sample producer):
   ```bash
   pip install -r etl-service/requirements.txt
   ```

2. **Run the sample producer:**
   ```bash
   python test_producer.py
   ```

Example output:
```bash
python test_producer.py                    
Starting sample producer...
Press Ctrl+C to stop

Sent event: user_login - ba302e7f-7a90-4835-98be-be75d4e733a5
Sent event: page_view - cb78932d-a1b4-4ec7-8724-5f9c70d81abf
Sent event: user_action - 7b4baaad-3fe0-442e-9bc1-12f098d03db8
Sent event: purchase - b66cfca5-61b7-4954-8c6b-28058fd6f9e7
Message delivered to data_events [0]
Message delivered to data_events [0]
Message delivered to data_events [0]
Message delivered to data_events [0]
Sent event: user_login - 9f616f7e-9245-4fef-b501-d55e7668141b
Sent event: page_view - b4c4997f-c727-4515-8ab5-daeab32b92cd
Sent event: user_action - dd60783c-4bbc-40e7-865e-750b21f4d3b2
Sent event: purchase - 44799d3f-7562-4e1c-ac63-1c778250d9f7
Message delivered to data_events [0]
Message delivered to data_events [0]
Message delivered to data_events [0]
Message delivered to data_events [0]
Sent event: user_login - b831bfc5-86b6-43fd-acf5-5272d07919f8
Sent event: page_view - 70c09f50-d7e1-4e49-965a-3bac879842d9
Sent event: user_action - 422e2dee-2a87-4e45-a6b9-36db7da519d2
```

3. **Check the database** for processed data:
   ```bash
   docker exec -it etl-postgres psql -U etl_user -d etl_db -c "SELECT * FROM events LIMIT 10;"
   ```

## Monitoring

- **Kafka UI**: http://localhost:8080

![Kafka UI](images/Kafka_ui.png)

- **PostgreSQL**: localhost:5432
  - Database: `etl_db`
  - User: `etl_user`
  - Password: `etl_password`

## Configuration

### Environment Variables

The ETL consumer can be configured using these environment variables:

- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address
- `KAFKA_TOPIC`: Topic to consume from
- `KAFKA_GROUP_ID`: Consumer group ID
- `DB_HOST`: PostgreSQL host
- `DB_PORT`: PostgreSQL port
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password

### Customizing the ETL Logic

Modify the `process_message()` method in `etl-service/consumer.py` to implement your specific data transformation logic.

## Database Schema

The stack creates these tables:

- `events`: Main table for processed events
- `raw_events`: Backup table for raw message data
- `event_summary`: View for analytics

## Troubleshooting

1. **"events" table doesn't exist**: The init script didn't run. Try:
   ```bash
   # Check if init-db.sql is in the right location
   ls -la init-db.sql
   
   # Recreate the database container
   docker-compose down
   docker volume rm etl-kafka-stack_postgres_data
   docker-compose up -d postgres
   
   # Or manually create the table
   docker exec -it etl-postgres psql -U etl_user -d etl_db -f /docker-entrypoint-initdb.d/init-db.sql
   ```

2. **Services not starting**: Check Docker logs
   ```bash
   docker-compose logs [service-name]
   ```

3. **Connection issues**: Ensure all services are healthy
   ```bash
   docker-compose ps
   ```

4. **Database connection**: Verify PostgreSQL is accessible
   ```bash
   docker exec -it etl-postgres pg_isready
   ```

5. **Check database initialization**:
   ```bash
   # List tables in the database
   docker exec -it etl-postgres psql -U etl_user -d etl_db -c "\dt"
   
   # Check if init script exists in container
   docker exec -it etl-postgres ls -la /docker-entrypoint-initdb.d/
   ```

## Scaling

To scale the ETL consumer:
```bash
docker-compose up -d --scale etl-consumer=3
```

## Stopping the Stack

```bash
docker-compose down -v  # -v removes volumes
```
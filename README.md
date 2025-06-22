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

3. **Check the database** for processed data:
   ```bash
   docker exec -it etl-postgres psql -U etl_user -d etl_db -c "SELECT * FROM events LIMIT 10;"
   ```

## Monitoring

- **Kafka UI**: http://localhost:8080
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
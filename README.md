# Event Ticketing API

A production-ready REST API for event management and ticket booking with automatic expiration and geospatial queries.

## Features

- 🎫 **Event Management**: Create and manage events with venue information
- 🎟️ **Ticket Reservations**: Reserve tickets with automatic expiration
- ⏰ **Auto-Expiration**: Background workers automatically expire unpaid tickets after 2 minutes
- 📍 **Geospatial Queries**: Find events near users based on location using PostGIS
- 🏗️ **Clean Architecture**: Repository and Service layer pattern with SOLID principles
- 🧪 **Comprehensive Tests**: Unit and integration tests with Pytest
- 🐳 **Fully Containerized**: Docker Compose setup for easy deployment

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with PostGIS extension
- **ORM**: SQLAlchemy (async)
- **Task Queue**: Celery + Redis
- **Migrations**: Alembic
- **Testing**: Pytest + httpx
- **Validation**: Pydantic v2

## Architecture

### Project Structure

```
event-ticketing-api/
├── app/
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── repositories/    # Data access layer
│   ├── services/        # Business logic layer
│   ├── api/v1/          # API endpoints
│   └── workers/         # Celery tasks
├── alembic/             # Database migrations
├── tests/               # Test suite
└── docker-compose.yml   # Container orchestration
```

### Design Patterns

- **Repository Pattern**: Separates data access logic from business logic
- **Service Layer**: Encapsulates business rules and orchestrates repositories
- **Dependency Injection**: Uses FastAPI's dependency system for clean separation
- **Domain-Driven Design**: Models reflect business domain concepts

## Models

### User
- `id` (UUID) - Primary key
- `name` (String) - User's full name
- `email` (String) - Unique email address
- `latitude`, `longitude` (Float) - User's location
- `location` (Geography) - PostGIS point for geospatial queries

### Event
- `id` (UUID) - Primary key
- `title` (String) - Event title
- `description` (String) - Event description
- `start_time`, `end_time` (DateTime with timezone)
- `total_tickets` (Integer) - Total available tickets
- `tickets_sold` (Integer) - Number of tickets sold
- `venue` (Composite) - Location, address, latitude, longitude
- `geo_location` (Geography) - PostGIS point for location queries

### Ticket
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to User
- `event_id` (UUID) - Foreign key to Event
- `status` (Enum) - `reserved`, `paid`, or `expired`
- `created_at` (DateTime with timezone)

## API Endpoints

### Events

```http
POST   /api/v1/events              # Create new event
GET    /api/v1/events              # List all events
GET    /api/v1/events/{id}         # Get event details
```

### Tickets

```http
POST   /api/v1/tickets             # Reserve a ticket
POST   /api/v1/tickets/{id}/pay    # Mark ticket as paid
```

### Users

```http
POST   /api/v1/users                          # Create user
GET    /api/v1/users/{id}/relevant-events    # Get nearby events
GET    /api/v1/users/{id}/tickets            # Get ticket history
```

## Setup and Installation

### Prerequisites

- Docker and Docker Compose
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd event-ticketing-platform-api
   ```

2. **Start all services with one command**
   ```bash
   docker-compose up -d
   ```

   This will automatically:
   - ✅ Pull and start PostgreSQL with PostGIS extension
   - ✅ Pull and start Redis
   - ✅ Build the API Docker image
   - ✅ Build the Worker Docker image
   - ✅ Run database migrations (Alembic)
   - ✅ Start the FastAPI application (with Gunicorn + Uvicorn)
   - ✅ Start Celery worker for task processing
   - ✅ Start Celery Beat for periodic tasks

3. **Verify services are running**
   ```bash
   docker-compose ps
   ```
   
   You should see 5 containers running:
   - `event_db` - PostgreSQL with PostGIS
   - `event_redis` - Redis
   - `eventticketingplatformapi` - FastAPI application
   - `event_worker` - Celery worker
   - `event_beat` - Celery Beat scheduler

4. **Access the API**
   - API: http://localhost:8000
   - Interactive docs (Swagger UI): http://localhost:8000/docs
   - Alternative docs (ReDoc): http://localhost:8000/redoc
   - Health check: http://localhost:8000/health

### Docker Services Explained

```yaml
services:
  db:              # PostgreSQL 15 with PostGIS 3.3
  redis:           # Redis 7 for Celery message queue
  api:             # FastAPI app (Gunicorn + Uvicorn workers)
  worker:          # Celery worker (processes background tasks)
  beat:            # Celery Beat (periodic task scheduler)
```

**Key Features:**
- **Health Checks**: Database and Redis have health checks to ensure proper startup order
- **Auto Migrations**: API service runs `alembic upgrade head` on startup
- **Hot Reload**: Code changes automatically reload the API (development mode)
- **Volume Mounting**: Source code mounted for development
- **Production Ready**: Uses Gunicorn with Uvicorn workers

### Environment Variables

The Docker setup uses these environment variables (no `.env` file needed):

```bash
# Database (async for app, sync for Alembic)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/eventdb
DATABASE_URL_SYNC=postgresql://postgres:postgres@db:5432/eventdb

# Redis & Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

To customize, create a `.env` file or modify `docker-compose.yml`.

### Common Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f                    # All services
docker-compose logs -f api                # API only
docker-compose logs -f worker             # Worker only
docker-compose logs -f beat               # Beat scheduler only

# Restart a service
docker-compose restart api

# Rebuild after code changes
docker-compose up -d --build

# Stop and remove everything (including volumes)
docker-compose down -v

# Execute commands in containers
docker-compose exec api bash              # Shell into API container
docker-compose exec api pytest            # Run tests
docker-compose exec api alembic upgrade head  # Run migrations
```

## Running Tests

### Using Docker (Recommended)

```bash
# Run all tests
docker-compose exec api pytest

# Run with verbose output
docker-compose exec api pytest -v

# Run with coverage report
docker-compose exec api pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec api pytest tests/test_tickets.py

# Run specific test class
docker-compose exec api pytest tests/test_tickets.py::TestTicketReservation

# Run specific test method
docker-compose exec api pytest tests/test_tickets.py::TestTicketReservation::test_reserve_ticket_success

# Run tests matching a pattern
docker-compose exec api pytest -k "ticket"

# View HTML coverage report
docker-compose exec api pytest --cov=app --cov-report=html
# Then open htmlcov/index.html in your browser
```

### Local Testing (Without Docker)

If running locally without Docker:

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install test dependencies
pip install -r requirements.txt

# Set test database URL
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/eventdb_test

# Run tests
pytest
pytest -v
pytest --cov=app
```

### Test Structure

```
tests/
├── conftest.py           # Pytest fixtures and configuration
├── test_events.py        # Event creation and listing tests
├── test_tickets.py       # Ticket reservation and payment tests
├── test_users.py         # User creation and geospatial tests
└── test_workers.py       # Celery task expiration tests
```

### What's Tested

✅ **Ticket Reservation Logic**
- Successful reservation
- Sold out validation
- Nonexistent event handling
- Tickets sold counter updates

✅ **Payment Processing**
- Mark ticket as paid
- Validate ticket status transitions
- Prevent double payment

✅ **Event Availability**
- Counter increments on reservation
- Counter decrements on expiration
- Sold out detection

✅ **Ticket Expiration**
- `is_expired()` method validation
- Repository expired ticket queries
- Service layer expiration logic
- Status transitions (reserved → expired)

✅ **Geospatial Queries**
- Find events near user location
- Distance calculations
- Radius filtering
- User without location handling

✅ **User Operations**
- User creation
- Duplicate email validation
- Ticket history retrieval

## Business Logic

### Ticket Reservation Flow

1. User reserves a ticket → Ticket status = `reserved`
2. `tickets_sold` counter increments atomically
3. Celery task scheduled to expire ticket in 2 minutes
4. If payment received → Ticket status = `paid`
5. If not paid within 2 minutes:
   - Background worker changes status to `expired`
   - `tickets_sold` counter decrements
   - Ticket becomes available again

### Automatic Expiration

Two mechanisms ensure tickets don't stay reserved indefinitely:

1. **Individual Task**: When a ticket is reserved, a delayed Celery task is scheduled
2. **Periodic Sweep**: Every 60 seconds, a Celery Beat task checks for expired tickets

This dual approach ensures reliability even if individual tasks fail.

### Geospatial Queries

Uses PostGIS for efficient location-based queries:

- Events stored with `GEOGRAPHY` type (lat/lng)
- Spatial index for fast proximity searches
- Distance calculations in kilometers
- Configurable search radius

## Database Migrations

```bash
# Create a new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback one migration
docker-compose exec api alembic downgrade -1
```

## Example Usage

### Create an Event

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tech Conference 2025",
    "description": "Annual technology conference",
    "start_time": "2025-12-01T09:00:00Z",
    "end_time": "2025-12-01T17:00:00Z",
    "total_tickets": 500,
    "venue": {
      "location": "Conference Center",
      "address": "123 Main St, Lagos, Nigeria",
      "latitude": 6.5244,
      "longitude": 3.3792
    }
  }'
```

### Create a User

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "latitude": 6.5244,
    "longitude": 3.3792
  }'
```

### Reserve a Ticket

```bash
curl -X POST http://localhost:8000/api/v1/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_UUID_HERE",
    "event_id": "EVENT_UUID_HERE"
  }'
```

### Get Nearby Events

```bash
curl "http://localhost:8000/api/v1/users/USER_UUID_HERE/relevant-events?radius_km=50"
```

## Monitoring

### Container Health

```bash
# Check running containers
docker-compose ps

# Check container health status
docker inspect --format='{{.State.Health.Status}}' event_db
docker inspect --format='{{.State.Health.Status}}' event_redis

# View resource usage
docker stats
```

### Application Logs

```bash
# View all logs (follow mode)
docker-compose logs -f

# API logs only
docker-compose logs -f api

# Worker logs (see ticket expiration tasks)
docker-compose logs -f worker

# Beat scheduler logs (periodic tasks)
docker-compose logs -f beat

# Database logs
docker-compose logs -f db

# Redis logs
docker-compose logs -f redis

# Last 100 lines
docker-compose logs --tail=100 api

# Logs since timestamp
docker-compose logs --since 2024-01-01T00:00:00 api
```

### Service Health Endpoints

```bash
# API health check
curl http://localhost:8000/health

# Response: {"status": "healthy"}

# Check API is running
curl http://localhost:8000/

# Response: {"message": "Event Ticketing API", "version": "1.0.0", "docs": "/docs"}
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d eventdb

# Run SQL queries
docker-compose exec db psql -U postgres -d eventdb -c "SELECT COUNT(*) FROM tickets;"

# Check PostGIS extension
docker-compose exec db psql -U postgres -d eventdb -c "SELECT PostGIS_version();"

# View all tables
docker-compose exec db psql -U postgres -d eventdb -c "\dt"
```

### Redis Monitoring

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Check Redis info
docker-compose exec redis redis-cli INFO

# Monitor real-time commands
docker-compose exec redis redis-cli MONITOR

# Check Celery queue
docker-compose exec redis redis-cli LLEN celery

# View all keys
docker-compose exec redis redis-cli KEYS "*"
```

### Celery Task Monitoring

```bash
# Check worker status
docker-compose exec worker celery -A app.workers.celery_app inspect active

# View registered tasks
docker-compose exec worker celery -A app.workers.celery_app inspect registered

# Check scheduled tasks
docker-compose exec worker celery -A app.workers.celery_app inspect scheduled

# View worker stats
docker-compose exec worker celery -A app.workers.celery_app inspect stats
```

## Development

### Local Development (without Docker)

1. Install PostgreSQL with PostGIS
2. Install Redis
3. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run migrations:
   ```bash
   alembic upgrade head
   ```
6. Start services:
   ```bash
   # Terminal 1: API
   uvicorn app.main:app --reload
   
   # Terminal 2: Celery Worker
   celery -A app.workers.celery_app worker --loglevel=info
   
   # Terminal 3: Celery Beat
   celery -A app.workers.celery_app beat --loglevel=info
   ```

## Key Design Decisions

### 1. Async SQLAlchemy
- Uses `AsyncSession` for non-blocking database operations
- Improves API throughput under load
- Compatible with FastAPI's async nature

### 2. Composite Venue Type
- Venue information grouped as a composite in SQLAlchemy
- Maintains atomicity of related fields
- Clean separation of concerns

### 3. Dual Expiration Strategy
- Individual task: Precise timing for each ticket
- Periodic sweep: Safety net for failed tasks
- Ensures no tickets are stuck in limbo

### 4. Geospatial Indexing
- PostGIS `GEOGRAPHY` type with GIST index
- Efficient proximity queries at scale
- Accurate distance calculations

### 5. Repository Pattern
- Separates data access from business logic
- Easy to test and mock
- Follows SOLID principles

## Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test API endpoints end-to-end
- **Service Tests**: Test business logic without HTTP layer
- **Worker Tests**: Test Celery task behavior

## Assumptions

1. **Timezones**: All times stored in UTC, client responsible for timezone conversion
2. **Coordinates**: Uses WGS84 (SRID 4326) coordinate system
3. **Concurrency**: Optimistic locking via `tickets_sold` counter
4. **Payment**: Simplified payment flow (real implementation would integrate payment gateway)
5. **Scale**: Designed for thousands of events and users (would need additional optimization for millions)

## Production Considerations

For production deployment, consider:

1. **Security**:
   - Add authentication (JWT, OAuth2)
   - Use environment variables for secrets
   - Enable HTTPS
   - Add rate limiting

2. **Performance**:
   - Add caching layer (Redis)
   - Implement connection pooling
   - Use read replicas for queries
   - Add CDN for static assets

3. **Monitoring**:
   - Add APM (DataDog, New Relic)
   - Set up error tracking (Sentry)
   - Implement structured logging
   - Create health check endpoints

4. **Infrastructure**:
   - Use managed database (RDS, Cloud SQL)
   - Implement auto-scaling
   - Set up CI/CD pipeline
   - Add backup and disaster recovery

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Support

For issues and questions, please open a GitHub issue.
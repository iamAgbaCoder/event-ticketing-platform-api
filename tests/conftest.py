import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport
from app.database import Base
from app.main import app
from app.routers.deps import get_db
from app.models import User, Event, Ticket
from datetime import datetime, timezone, timedelta
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
import uuid

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/eventdb_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create a test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        # Enable PostGIS
        await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_user(db_session: AsyncSession) -> User:
    """Create a sample user for testing"""
    user = User(
        id=uuid.uuid4(),
        name="Test User",
        email="test@example.com",
        latitude=6.5244,  # Ibadan, Nigeria
        longitude=3.3792,
        location=from_shape(Point(3.3792, 6.5244), srid=4326),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_event(db_session: AsyncSession) -> Event:
    """Create a sample event for testing"""
    now = datetime.now(timezone.utc)
    event = Event(
        id=uuid.uuid4(),
        title="Tech Conference 2025",
        description="Annual technology conference",
        start_time=now + timedelta(days=30),
        end_time=now + timedelta(days=30, hours=8),
        total_tickets=100,
        tickets_sold=0,
        venue_location="Conference Center",
        venue_address="123 Main St, Ibadan, Nigeria",
        venue_latitude=6.5244,
        venue_longitude=3.3792,
        geo_location=from_shape(Point(3.3792, 6.5244), srid=4326),
    )
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)
    return event

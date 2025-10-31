import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Event
from datetime import datetime, timezone, timedelta
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
import uuid


@pytest.mark.asyncio
class TestUsers:

    async def test_create_user(self, client: AsyncClient):
        """Test creating a new user"""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "latitude": 6.5244,
            "longitude": 3.3792,
        }

        response = await client.post("/api/v1/users", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["latitude"] == 6.5244
        assert data["longitude"] == 3.3792
        assert "id" in data

    async def test_create_user_duplicate_email(
        self, client: AsyncClient, sample_user: User
    ):
        """Test creating a user with duplicate email fails"""
        user_data = {
            "name": "Another User",
            "email": sample_user.email,
            "latitude": 6.5244,
            "longitude": 3.3792,
        }

        response = await client.post("/api/v1/users", json=user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestRelevantEvents:

    async def test_get_relevant_events_by_location(
        self, client: AsyncClient, db_session: AsyncSession, sample_user: User
    ):
        """Test getting events relevant to user's location"""
        now = datetime.now(timezone.utc)

        # Create events at different distances
        # Event 1: Very close (same location as user)
        close_event = Event(
            id=uuid.uuid4(),
            title="Nearby Event",
            description="Close to user",
            start_time=now + timedelta(days=7),
            end_time=now + timedelta(days=7, hours=4),
            total_tickets=100,
            tickets_sold=0,
            venue_location="Close Venue",
            venue_address="123 Close St",
            venue_latitude=6.5244,  # Same as user
            venue_longitude=3.3792,
            geo_location=from_shape(Point(3.3792, 6.5244), srid=4326),
        )

        # Event 2: Far away (Lagos - about 140km from Ibadan)
        far_event = Event(
            id=uuid.uuid4(),
            title="Far Event",
            description="Far from user",
            start_time=now + timedelta(days=14),
            end_time=now + timedelta(days=14, hours=4),
            total_tickets=100,
            tickets_sold=0,
            venue_location="Far Venue",
            venue_address="456 Far St",
            venue_latitude=6.4541,  # Lagos coordinates
            venue_longitude=3.3947,
            geo_location=from_shape(Point(3.3947, 6.4541), srid=4326),
        )

        db_session.add(close_event)
        db_session.add(far_event)
        await db_session.commit()

        # Get relevant events within 50km
        response = await client.get(
            f"/api/v1/users/{sample_user.id}/relevant-events?radius_km=50"
        )

        assert response.status_code == 200
        data = response.json()

        # Should return only the close event
        assert len(data) == 1
        assert data[0]["title"] == "Nearby Event"
        assert "distance_km" in data[0]
        assert data[0]["distance_km"] < 1  # Very close

    async def test_get_relevant_events_user_without_location(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test getting relevant events for user without location fails"""
        user = User(
            id=uuid.uuid4(),
            name="User Without Location",
            email="nolocation@example.com",
            latitude=None,
            longitude=None,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.get(f"/api/v1/users/{user.id}/relevant-events")

        assert response.status_code == 400
        assert "location not set" in response.json()["detail"].lower()

    async def test_get_relevant_events_nonexistent_user(self, client: AsyncClient):
        """Test getting relevant events for nonexistent user fails"""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/users/{fake_id}/relevant-events")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestUserTicketHistory:

    async def test_get_user_ticket_history(
        self, client: AsyncClient, sample_user: User, sample_event: Event
    ):
        """Test getting user's ticket history"""
        # First create a ticket
        ticket_data = {"user_id": str(sample_user.id), "event_id": str(sample_event.id)}
        await client.post("/api/v1/tickets", json=ticket_data)

        # Get ticket history
        response = await client.get(f"/api/v1/users/{sample_user.id}/tickets")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["event_title"] == sample_event.title
        assert data[0]["venue_location"] == sample_event.venue_location

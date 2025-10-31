import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from app.models import Event


@pytest.mark.asyncio
class TestEvents:

    async def test_create_event(self, client: AsyncClient):
        """Test creating a new event"""
        now = datetime.now(timezone.utc)
        event_data = {
            "title": "Music Festival",
            "description": "Annual music festival",
            "start_time": (now + timedelta(days=60)).isoformat(),
            "end_time": (now + timedelta(days=60, hours=10)).isoformat(),
            "total_tickets": 500,
            "venue": {
                "location": "Stadium",
                "address": "456 Event Ave, Lagos, Nigeria",
                "latitude": 6.5244,
                "longitude": 3.3792,
            },
        }

        response = await client.post("/api/v1/events", json=event_data)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Music Festival"
        assert data["total_tickets"] == 500
        assert data["tickets_sold"] == 0
        assert data["available_tickets"] == 500
        assert "id" in data

    async def test_list_events(self, client: AsyncClient, sample_event: Event):
        """Test listing all events"""
        response = await client.get("/api/v1/events")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["title"] == sample_event.title

    async def test_get_event_by_id(self, client: AsyncClient, sample_event: Event):
        """Test getting a specific event"""
        response = await client.get(f"/api/v1/events/{sample_event.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_event.id)
        assert data["title"] == sample_event.title

    async def test_get_nonexistent_event(self, client: AsyncClient):
        """Test getting an event that doesn't exist"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/events/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

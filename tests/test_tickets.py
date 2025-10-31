import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Event, Ticket, TicketStatus
from app.services.ticket import TicketService
from app.repositories.event import EventRepository
from datetime import datetime, timezone, timedelta
import uuid


@pytest.mark.asyncio
class TestTicketReservation:

    async def test_reserve_ticket_success(
        self, client: AsyncClient, sample_user: User, sample_event: Event
    ):
        """Test successful ticket reservation"""
        ticket_data = {"user_id": str(sample_user.id), "event_id": str(sample_event.id)}

        response = await client.post("/api/v1/tickets", json=ticket_data)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "reserved"
        assert data["user_id"] == str(sample_user.id)
        assert data["event_id"] == str(sample_event.id)
        assert "id" in data
        assert "created_at" in data

    async def test_reserve_ticket_sold_out(
        self, client: AsyncClient, db_session: AsyncSession, sample_user: User
    ):
        """Test reservation fails when event is sold out"""
        now = datetime.now(timezone.utc)
        sold_out_event = Event(
            id=uuid.uuid4(),
            title="Sold Out Event",
            description="This event is sold out",
            start_time=now + timedelta(days=7),
            end_time=now + timedelta(days=7, hours=4),
            total_tickets=10,
            tickets_sold=10,  # Already sold out
            venue_location="Venue",
            venue_address="Address",
            venue_latitude=6.5244,
            venue_longitude=3.3792,
            geo_location="SRID=4326;POINT(3.3792 6.5244)",
        )
        db_session.add(sold_out_event)
        await db_session.commit()

        ticket_data = {
            "user_id": str(sample_user.id),
            "event_id": str(sold_out_event.id),
        }

        response = await client.post("/api/v1/tickets", json=ticket_data)

        assert response.status_code == 400
        assert "sold out" in response.json()["detail"].lower()

    async def test_reserve_ticket_nonexistent_event(
        self, client: AsyncClient, sample_user: User
    ):
        """Test reservation fails for nonexistent event"""
        fake_event_id = str(uuid.uuid4())
        ticket_data = {"user_id": str(sample_user.id), "event_id": fake_event_id}

        response = await client.post("/api/v1/tickets", json=ticket_data)

        assert response.status_code == 404


@pytest.mark.asyncio
class TestTicketPayment:

    async def test_mark_ticket_paid_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        sample_user: User,
        sample_event: Event,
    ):
        """Test marking a reserved ticket as paid"""
        # First, reserve a ticket
        ticket = Ticket(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            event_id=sample_event.id,
            status=TicketStatus.RESERVED,
        )
        db_session.add(ticket)
        await db_session.commit()

        # Then mark it as paid
        response = await client.post(f"/api/v1/tickets/{ticket.id}/pay")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paid"
        assert data["id"] == str(ticket.id)

    async def test_mark_paid_ticket_as_paid_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        sample_user: User,
        sample_event: Event,
    ):
        """Test marking an already paid ticket as paid fails"""
        ticket = Ticket(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            event_id=sample_event.id,
            status=TicketStatus.PAID,
        )
        db_session.add(ticket)
        await db_session.commit()

        response = await client.post(f"/api/v1/tickets/{ticket.id}/pay")

        assert response.status_code == 400
        assert "cannot mark ticket as paid" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestEventAvailability:

    async def test_tickets_sold_increments_on_reservation(
        self, db_session: AsyncSession, sample_user: User, sample_event: Event
    ):
        """Test that tickets_sold increments when a ticket is reserved"""
        initial_sold = sample_event.tickets_sold

        service = TicketService(db_session)
        from app.schemas.ticket import TicketCreate

        await service.reserve_ticket(
            TicketCreate(user_id=sample_user.id, event_id=sample_event.id)
        )

        # Refresh event
        await db_session.refresh(sample_event)

        assert sample_event.tickets_sold == initial_sold + 1

    async def test_tickets_sold_decrements_on_expiration(
        self, db_session: AsyncSession, sample_user: User, sample_event: Event
    ):
        """Test that tickets_sold decrements when a ticket expires"""
        # Create a reserved ticket
        ticket = Ticket(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            event_id=sample_event.id,
            status=TicketStatus.RESERVED,
        )
        db_session.add(ticket)

        # Manually increment tickets_sold
        sample_event.tickets_sold += 1
        await db_session.commit()

        initial_sold = sample_event.tickets_sold

        # Expire the ticket
        service = TicketService(db_session)
        await service.expire_ticket(ticket.id)

        # Refresh event
        await db_session.refresh(sample_event)

        assert sample_event.tickets_sold == initial_sold - 1

from repositories.ticket import TicketRepository
from repositories.event import EventRepository
from models.ticket import Ticket, TicketStatus
from schemas.ticket import TicketCreate, TicketResponse, TicketWithEventResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from fastapi import HTTPException, status


class TicketService:
    def __init__(self, db: AsyncSession):
        self.ticket_repo = TicketRepository(db)
        self.event_repo = EventRepository(db)

    async def reserve_ticket(self, ticket_data: TicketCreate) -> TicketResponse:
        """
        Reserve a ticket for a user.
        Business rules:
        - Event must exist
        - Event must not be sold out
        - Ticket is created with RESERVED status
        """
        # Check if event exists
        event = await self.event_repo.get_by_id(ticket_data.event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
            )

        # Check if event is sold out
        if event.is_sold_out:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Event is sold out"
            )

        # Create ticket with RESERVED status
        ticket = Ticket(
            user_id=ticket_data.user_id,
            event_id=ticket_data.event_id,
            status=TicketStatus.RESERVED,
        )

        created_ticket = await self.ticket_repo.create(ticket)

        # Increment tickets_sold counter
        await self.event_repo.increment_tickets_sold(ticket_data.event_id)

        # Schedule expiration task (will be handled by Celery)
        from workers.tasks import expire_ticket

        expire_ticket.apply_async(
            args=[str(created_ticket.id)], countdown=120  # 2 minutes
        )

        return self._to_response(created_ticket)

    async def mark_ticket_paid(self, ticket_id: UUID) -> TicketResponse:
        """
        Mark a ticket as paid.
        Business rules:
        - Ticket must exist
        - Ticket must be in RESERVED status
        """
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
            )

        if ticket.status != TicketStatus.RESERVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark ticket as paid. Current status: {ticket.status}",
            )

        # Update ticket status to PAID
        updated_ticket = await self.ticket_repo.update_status(
            ticket_id, TicketStatus.PAID
        )

        return self._to_response(updated_ticket)

    async def get_user_ticket_history(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[TicketWithEventResponse]:
        """Get ticket history for a user"""
        tickets = await self.ticket_repo.get_user_tickets(
            user_id=user_id, skip=skip, limit=limit
        )

        return [
            TicketWithEventResponse(
                id=ticket.id,
                user_id=ticket.user_id,
                event_id=ticket.event_id,
                status=ticket.status,
                created_at=ticket.created_at,
                event_title=ticket.event.title,
                event_start_time=ticket.event.start_time,
                venue_location=ticket.event.venue_location,
            )
            for ticket in tickets
        ]

    async def expire_ticket(self, ticket_id: UUID) -> bool:
        """
        Expire a ticket if it's still in RESERVED status.
        Returns True if ticket was expired, False otherwise.
        """
        ticket = await self.ticket_repo.get_by_id_with_event(ticket_id)

        if not ticket:
            return False

        # Only expire if still in RESERVED status
        if ticket.status != TicketStatus.RESERVED:
            return False

        # Update ticket status to EXPIRED
        await self.ticket_repo.update_status(ticket_id, TicketStatus.EXPIRED)

        # Decrement tickets_sold counter
        await self.event_repo.decrement_tickets_sold(ticket.event_id)

        return True

    def _to_response(self, ticket: Ticket) -> TicketResponse:
        """Convert Ticket model to response schema"""
        return TicketResponse(
            id=ticket.id,
            user_id=ticket.user_id,
            event_id=ticket.event_id,
            status=ticket.status,
            created_at=ticket.created_at,
        )

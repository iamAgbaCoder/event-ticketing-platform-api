from app.repositories.base import BaseRepository
from app.models.ticket import Ticket, TicketStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta


class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, db: AsyncSession):
        super().__init__(Ticket, db)

    async def get_by_id_with_event(self, ticket_id: UUID) -> Optional[Ticket]:
        """Get ticket with event relationship loaded"""
        result = await self.db.execute(
            select(Ticket)
            .options(joinedload(Ticket.event))
            .where(Ticket.id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def get_user_tickets(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Ticket]:
        """Get all tickets for a user with event details"""
        result = await self.db.execute(
            select(Ticket)
            .options(joinedload(Ticket.event))
            .where(Ticket.user_id == user_id)
            .order_by(Ticket.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_expired_tickets(
        self, timeout_seconds: int = 120, limit: int = 100
    ) -> List[Ticket]:
        """Get tickets that are reserved but have expired"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)

        result = await self.db.execute(
            select(Ticket)
            .options(joinedload(Ticket.event))
            .where(
                Ticket.status == TicketStatus.RESERVED, Ticket.created_at <= cutoff_time
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self, ticket_id: UUID, new_status: TicketStatus
    ) -> Optional[Ticket]:
        """Update ticket status"""
        ticket = await self.get_by_id(ticket_id)
        if ticket:
            ticket.status = new_status
            await self.db.commit()
            await self.db.refresh(ticket)
        return ticket

    async def count_by_event(
        self, event_id: UUID, status: Optional[TicketStatus] = None
    ) -> int:
        """Count tickets for an event, optionally filtered by status"""
        from sqlalchemy import func

        query = (
            select(func.count()).select_from(Ticket).where(Ticket.event_id == event_id)
        )

        if status:
            query = query.where(Ticket.status == status)

        result = await self.db.execute(query)
        return result.scalar_one()

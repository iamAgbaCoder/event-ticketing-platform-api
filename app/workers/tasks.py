from app.workers.celery import celery_app
from app.config import get_settings
from uuid import UUID
import asyncio

settings = get_settings()


@celery_app.task(name="app.workers.tasks.expire_ticket")
def expire_ticket(ticket_id: str):
    """
    Expire a specific ticket if it's still in RESERVED status.
    This task is scheduled when a ticket is created.
    """
    from database import AsyncSessionLocal
    from services.ticket import TicketService

    async def _expire():
        async with AsyncSessionLocal() as session:
            service = TicketService(session)
            try:
                ticket_uuid = UUID(ticket_id)
                expired = await service.expire_ticket(ticket_uuid)
                if expired:
                    return f"Ticket {ticket_id} expired successfully"
                else:
                    return f"Ticket {ticket_id} was not expired (already paid or not found)"
            except Exception as e:
                return f"Error expiring ticket {ticket_id}: {str(e)}"

    # Run the async function
    return asyncio.run(_expire())


@celery_app.task(name="app.workers.tasks.expire_reserved_tickets")
def expire_reserved_tickets():
    """
    Periodic task to expire all reserved tickets that have exceeded the timeout.
    Runs every minute as a backup to ensure no tickets are stuck in RESERVED state.
    """
    from database import AsyncSessionLocal
    from repositories.ticket import TicketRepository
    from repositories.event import EventRepository
    from models.ticket import TicketStatus

    async def _expire_batch():
        async with AsyncSessionLocal() as session:
            ticket_repo = TicketRepository(session)
            event_repo = EventRepository(session)

            try:
                # Get expired tickets
                expired_tickets = await ticket_repo.get_expired_tickets(
                    timeout_seconds=settings.ticket_reservation_timeout, limit=100
                )

                expired_count = 0
                for ticket in expired_tickets:
                    # Update status
                    await ticket_repo.update_status(ticket.id, TicketStatus.EXPIRED)

                    # Decrement tickets_sold
                    await event_repo.decrement_tickets_sold(ticket.event_id)

                    expired_count += 1

                return f"Expired {expired_count} tickets"
            except Exception as e:
                return f"Error in batch expiration: {str(e)}"

    # Run the async function
    return asyncio.run(_expire_batch())

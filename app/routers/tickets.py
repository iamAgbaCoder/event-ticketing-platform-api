from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from routers.deps import get_db
from services.ticket import TicketService
from schemas.ticket import TicketCreate, TicketResponse, PaymentRequest
from uuid import UUID

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def reserve_ticket(ticket_data: TicketCreate, db: AsyncSession = Depends(get_db)):
    """
    Reserve a ticket for a user.
    Ticket will be automatically expired if not paid within 2 minutes.
    """
    service = TicketService(db)
    return await service.reserve_ticket(ticket_data)


@router.post("/{ticket_id}/pay", response_model=TicketResponse)
async def mark_ticket_paid(ticket_id: UUID, db: AsyncSession = Depends(get_db)):
    """Mark a reserved ticket as paid"""
    service = TicketService(db)
    return await service.mark_ticket_paid(ticket_id)

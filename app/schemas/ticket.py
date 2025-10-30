from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from models.ticket import TicketStatus
from typing import Optional


class TicketBase(BaseModel):
    user_id: UUID
    event_id: UUID


class TicketCreate(TicketBase):
    pass


class TicketResponse(TicketBase):
    id: UUID
    status: TicketStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketWithEventResponse(TicketResponse):
    event_title: str
    event_start_time: datetime
    venue_location: str


class PaymentRequest(BaseModel):
    ticket_id: UUID


class TicketHistoryResponse(BaseModel):
    tickets: list[TicketWithEventResponse]
    total: int

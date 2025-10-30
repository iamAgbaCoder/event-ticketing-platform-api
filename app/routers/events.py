from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from routers.deps import get_db
from services.event import EventService
from schemas.event import EventCreate, EventResponse, EventListResponse
from typing import List
from uuid import UUID

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event_data: EventCreate, db: AsyncSession = Depends(get_db)):
    """Create a new event"""
    service = EventService(db)
    return await service.create_event(event_data)


@router.get("", response_model=List[EventResponse])
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all events"""
    service = EventService(db)
    return await service.list_events(skip=skip, limit=limit)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific event by ID"""
    service = EventService(db)
    return await service.get_event(event_id)

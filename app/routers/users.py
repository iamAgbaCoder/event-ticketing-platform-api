from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.routers.deps import get_db
from app.services.event import EventService
from app.services.ticket import TicketService
from app.repositories.user import UserRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.event import EventListResponse
from app.schemas.ticket import TicketWithEventResponse
from app.config import get_settings
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from typing import List
from uuid import UUID

# fetch settings
settings = get_settings()

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user"""
    user_repo = UserRepository(db)

    # Check if email already exists
    if await user_repo.email_exists(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create user
    user = User(
        name=user_data.name,
        email=user_data.email,
        latitude=user_data.latitude,
        longitude=user_data.longitude,
    )

    # Set geospatial location if coordinates provided
    if settings.database_url.startswith("sqlite"):  # for testing
        user.location = f"{user_data.latitude},{user_data.longitude}"
    else:
        if user_data.latitude is not None and user_data.longitude is not None:
            user.location = from_shape(
                Point(user_data.longitude, user_data.latitude), srid=4326
            )

    created_user = await user_repo.create(user)
    db.add(created_user)
    await db.commit()  # Ensure the commit happens
    await db.refresh(user)  # refresh to get updated values
    return UserResponse.model_validate(created_user)


@router.get("/{user_id}/relevant-events", response_model=List[EventListResponse])
async def get_relevant_events(
    user_id: UUID,
    radius_km: float = Query(settings.default_search_radius_km, ge=1, le=500),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get events relevant to a user based on their location.
    Returns events within the specified radius, ordered by distance.
    """
    user_repo = UserRepository(db)
    event_service = EventService(db)

    # Get user
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if user has location set
    if user.latitude is None or user.longitude is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User location not set. Please update user profile with location.",
        )

    # Get relevant events
    return await event_service.get_relevant_events(
        user_latitude=user.latitude,
        user_longitude=user.longitude,
        radius_km=radius_km,
        skip=skip,
        limit=limit,
    )


@router.get("/{user_id}/tickets", response_model=List[TicketWithEventResponse])
async def get_user_ticket_history(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get ticket purchase history for a user"""
    ticket_service = TicketService(db)
    return await ticket_service.get_user_ticket_history(
        user_id=user_id, skip=skip, limit=limit
    )

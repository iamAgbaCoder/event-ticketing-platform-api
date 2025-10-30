from repositories.event import EventRepository
from models.event import Event
from schemas.event import EventCreate, EventUpdate, EventResponse, EventListResponse
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status


class EventService:
    def __init__(self, db: AsyncSession):
        self.repository = EventRepository(db)

    async def create_event(self, event_data: EventCreate) -> EventResponse:
        """Create a new event"""
        # Create the Event model instance
        event = Event(
            title=event_data.title,
            description=event_data.description,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            total_tickets=event_data.total_tickets,
            tickets_sold=0,
            venue_location=event_data.venue.location,
            venue_address=event_data.venue.address,
            venue_latitude=event_data.venue.latitude,
            venue_longitude=event_data.venue.longitude,
            geo_location=from_shape(
                Point(event_data.venue.longitude, event_data.venue.latitude), srid=4326
            ),
        )

        created_event = await self.repository.create(event)
        return self._to_response(created_event)

    async def get_event(self, event_id: UUID) -> EventResponse:
        """Get event by ID"""
        event = await self.repository.get_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
            )
        return self._to_response(event)

    async def list_events(self, skip: int = 0, limit: int = 100) -> List[EventResponse]:
        """List all events"""
        events = await self.repository.get_all(skip=skip, limit=limit)
        return [self._to_response(event) for event in events]

    async def get_relevant_events(
        self,
        user_latitude: float,
        user_longitude: float,
        radius_km: float = 50.0,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EventListResponse]:
        """Get events relevant to user's location"""
        events_with_distance = await self.repository.get_events_near_location(
            latitude=user_latitude,
            longitude=user_longitude,
            radius_km=radius_km,
            skip=skip,
            limit=limit,
        )

        return [
            self._to_list_response(event, distance)
            for event, distance in events_with_distance
        ]

    def _to_response(self, event: Event) -> EventResponse:
        """Convert Event model to response schema"""
        from app.schemas.event import VenueSchema

        return EventResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            total_tickets=event.total_tickets,
            tickets_sold=event.tickets_sold,
            available_tickets=event.available_tickets,
            venue=VenueSchema(
                location=event.venue_location,
                address=event.venue_address,
                latitude=event.venue_latitude,
                longitude=event.venue_longitude,
            ),
        )

    def _to_list_response(self, event: Event, distance_km: float) -> EventListResponse:
        """Convert Event model to list response with distance"""
        from app.schemas.event import VenueSchema

        return EventListResponse(
            id=event.id,
            title=event.title,
            start_time=event.start_time,
            end_time=event.end_time,
            available_tickets=event.available_tickets,
            distance_km=round(distance_km, 2),
            venue=VenueSchema(
                location=event.venue_location,
                address=event.venue_address,
                latitude=event.venue_latitude,
                longitude=event.venue_longitude,
            ),
        )

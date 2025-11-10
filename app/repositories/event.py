from app.repositories.base import BaseRepository
from app.models.event import Event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_Distance
from typing import List, Tuple, Optional
from uuid import UUID


class EventRepository(BaseRepository[Event]):
    def __init__(self, db: AsyncSession):
        super().__init__(Event, db)

    async def get_events_near_location(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 50.0,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Tuple[Event, float]]:
        """
        Get events within a radius of a location, ordered by distance.
        Returns list of tuples: (event, distance_in_km)
        """
        # Create a point from lat/lng
        # user_point = ST_MakePoint(longitude, latitude, type_=text("Geography"))
        user_point = ST_MakePoint(longitude, latitude).ST_SetSRID(4326)

        # Calculate distance in meters and convert to km
        distance_expr = ST_Distance(Event.geo_location, user_point) / 1000.0

        # Query events within radius, ordered by distance
        query = (
            select(Event, distance_expr.label("distance_km"))
            .where(
                ST_DWithin(
                    Event.geo_location,
                    user_point,
                    radius_km * 1000,  # Convert km to meters
                )
            )
            .order_by(text("distance_km"))
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return [(row[0], row[1]) for row in result.all()]

    async def increment_tickets_sold(
        self, event_id: UUID, amount: int = 1
    ) -> Optional[Event]:
        """Atomically increment tickets_sold counter"""
        event = await self.get_by_id(event_id)
        if event:
            event.tickets_sold += amount
            await self.db.commit()
            await self.db.refresh(event)
        return event

    async def decrement_tickets_sold(
        self, event_id: UUID, amount: int = 1
    ) -> Optional[Event]:
        """Atomically decrement tickets_sold counter"""
        event = await self.get_by_id(event_id)
        if event:
            event.tickets_sold = max(0, event.tickets_sold - amount)
            await self.db.commit()
            await self.db.refresh(event)
        return event

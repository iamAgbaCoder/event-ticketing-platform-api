from sqlalchemy import Column, String, Integer, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship, composite
from geoalchemy2 import Geography
from datetime import datetime
from database import Base
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.ticket import Ticket


class Venue:
    """Composite type for venue information"""

    def __init__(
        self,
        location: str,
        address: str,
        latitude: float = None,
        longitude: float = None,
    ):
        self.location = location
        self.address = address
        self.latitude = latitude
        self.longitude = longitude

    def __composite_values__(self):
        return self.location, self.address, self.latitude, self.longitude

    def __repr__(self):
        return f"Venue(location={self.location}, address={self.address})"

    def __eq__(self, other):
        return (
            isinstance(other, Venue)
            and other.location == self.location
            and other.address == self.address
            and other.latitude == self.latitude
            and other.longitude == self.longitude
        )

    def __ne__(self, other):
        return not self.__eq__(other)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_tickets: Mapped[int] = mapped_column(Integer, nullable=False)
    tickets_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Venue composite
    venue_location: Mapped[str] = mapped_column(String(255), nullable=False)
    venue_address: Mapped[str] = mapped_column(String(500), nullable=False)
    venue_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    venue_longitude: Mapped[float] = mapped_column(Float, nullable=False)

    venue: Mapped[Venue] = composite(
        Venue, venue_location, venue_address, venue_latitude, venue_longitude
    )

    # Geospatial column for efficient location-based queries
    # geo_location = mapped_column(
    #     Geography(geometry_type="POINT", srid=4326), nullable=False, index=True
    # )
    # for testing:
    geo_location = Column(String, nullable=True)

    # Relationships
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="event")

    @property
    def available_tickets(self) -> int:
        return self.total_tickets - self.tickets_sold

    @property
    def is_sold_out(self) -> bool:
        return self.tickets_sold >= self.total_tickets

    def __repr__(self):
        return f"<Event(id={self.id}, title={self.title}, available={self.available_tickets})>"

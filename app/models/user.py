from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography
from database import Base
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.ticket import Ticket


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    # Geospatial: Store user's location for personalized event recommendations
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True, index=True
    )

    # Relationships
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

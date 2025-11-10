from sqlalchemy import Column, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography
from app.database import Base
import uuid
import os
from typing import TYPE_CHECKING
from utils.logger import setup_logger
from app.config import get_settings

settings = get_settings()
logger = setup_logger(__name__)

if TYPE_CHECKING:
    from app.models.ticket import Ticket


IS_SQLITE = "sqlite" in settings.database_url
logger.info(f"USING IS_SQLITE: {IS_SQLITE} {settings.database_url}")


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

    # Use Geography only in Postgres
    if not IS_SQLITE:
        location = mapped_column(
            Geography(geometry_type="POINT", srid=4326), nullable=True, index=True
        )
    else:
        location = Column(String, nullable=True)  # fallback for SQLite

    # Relationships
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

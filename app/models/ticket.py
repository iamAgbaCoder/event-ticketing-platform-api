from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from enum import Enum
from app.database import Base
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User
    from models.event import Event


class TicketStatus(str, Enum):
    RESERVED = "reserved"
    PAID = "paid"
    EXPIRED = "expired"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id"), nullable=False, index=True
    )
    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus, native_enum=False),
        default=TicketStatus.RESERVED,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tickets")
    event: Mapped["Event"] = relationship("Event", back_populates="tickets")

    def is_expired(self, timeout_seconds: int = 120) -> bool:
        """Check if ticket reservation has expired"""
        if self.status != TicketStatus.RESERVED:
            return False

        now = datetime.now(timezone.utc)
        elapsed = (now - self.created_at).total_seconds()
        return elapsed > timeout_seconds

    def __repr__(self):
        return f"<Ticket(id={self.id}, status={self.status}, user_id={self.user_id})>"

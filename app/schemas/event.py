from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional


class VenueSchema(BaseModel):
    location: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=1, max_length=500)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    total_tickets: int = Field(..., gt=0)
    venue: VenueSchema

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v, info):
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_tickets: Optional[int] = Field(None, gt=0)
    venue: Optional[VenueSchema] = None


class EventResponse(EventBase):
    id: UUID
    tickets_sold: int
    available_tickets: int

    model_config = {"from_attributes": True}

    @property
    def is_sold_out(self) -> bool:
        return self.available_tickets <= 0


class EventListResponse(BaseModel):
    id: UUID
    title: str
    start_time: datetime
    end_time: datetime
    venue: VenueSchema
    available_tickets: int
    distance_km: Optional[float] = None  # Distance from user's location

    model_config = {"from_attributes": True}

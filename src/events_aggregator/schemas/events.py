from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventPlaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    city: str
    address: str


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    place: EventPlaceResponse
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class EventsResponse(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventResponse]

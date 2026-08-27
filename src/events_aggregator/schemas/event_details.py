from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventPlaceDetails(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    city: str
    address: str
    seats_pattern: str


class EventDetails(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    place: EventPlaceDetails
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int
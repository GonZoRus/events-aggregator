import uuid

from pydantic import BaseModel, EmailStr


class TicketPost(BaseModel):
    event_id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    seat: str

class TicketResponse(BaseModel):
    ticket_id: uuid.UUID
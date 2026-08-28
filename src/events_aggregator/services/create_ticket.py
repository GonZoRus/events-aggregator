import uuid

import httpx

from events_aggregator.clients.events_provider import EventsProviderClient
from events_aggregator.repositories.ticket import TicketRepository
from events_aggregator.services.exceptions import (
    EventNotFound,
    ProviderUnavailable,
    SeatAlreadyTaken,
)


class CreateTicketUsecase:
    def __init__(
        self, client: EventsProviderClient, ticket_repository: TicketRepository
    ):
        self.client = client
        self.ticket_repository = ticket_repository

    async def execute(
        self,
        event_id: uuid.UUID,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str:
        try:
            ticket_id = await self.client.register(
                event_id=event_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                seat=seat,
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise SeatAlreadyTaken()
            if e.response.status_code == 404:
                raise EventNotFound()
            if e.response.status_code == 401:
                raise ProviderUnavailable()
            raise
        except httpx.RequestError:
            raise ProviderUnavailable()

        try:
            self.ticket_repository.create_ticket(ticket_id, event_id, seat)
            await self.ticket_repository.commit()
        except Exception:
            await self.ticket_repository.rollback()
            raise

        return ticket_id

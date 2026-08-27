import uuid

import httpx

from events_aggregator.clients.events_provider import EventsProviderClient
from events_aggregator.repositories.ticket import TicketRepository
from events_aggregator.services.exceptions import ProviderUnavailable, TicketNotFound


class DeleteTicketUsecase:
    def __init__(
        self, client: EventsProviderClient, ticket_repository: TicketRepository
    ):
        self.client = client
        self.ticket_repository = ticket_repository

    async def execute(self, ticket_id: uuid.UUID):
        ticket = await self.ticket_repository.get_ticket_by_id(ticket_id)

        if ticket is None:
            raise TicketNotFound()

        for attempt in range(2):
            try:
                await self.client.unregister(
                    event_id=ticket.event_id, ticket_id=ticket.ticket_id
                )
                break
            except httpx.RequestError:
                if attempt == 1:
                    raise ProviderUnavailable()
            except httpx.HTTPStatusError:
                raise ProviderUnavailable()

        try:
            await self.ticket_repository.delete_ticket(ticket)
            await self.ticket_repository.commit()
        except Exception:
            await self.ticket_repository.rollback()
            raise

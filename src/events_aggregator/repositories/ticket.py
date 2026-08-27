import uuid

from events_aggregator.models.tickets import Ticket


class TicketRepository:
    def __init__(self, session):
        self.session = session

    def create_ticket(self, ticket_id: uuid.UUID, event_id: uuid.UUID, seat: str):

        ticket = Ticket(ticket_id=ticket_id, event_id=event_id, seat=seat)
        self.session.add(ticket)

    async def get_ticket_by_id(self, ticket_id: uuid.UUID) -> Ticket | None:
        ticket = await self.session.get(Ticket, ticket_id)
        return ticket

    async def delete_ticket(self, ticket: Ticket) -> None:
        await self.session.delete(ticket)

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

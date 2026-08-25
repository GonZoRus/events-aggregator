from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from events_aggregator.models import Event


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_event_by_id(self, event_id: UUID) -> Event | None:
        event = await self.session.get(Event, event_id)
        return event

    def add_event(self, event: Event):
        self.session.add(event)

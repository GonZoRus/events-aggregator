from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from events_aggregator.models import Event


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_event_by_id(self, event_id: UUID) -> Event | None:
        event = await self.session.get(Event, event_id)
        return event

    def add_event(self, event: Event):
        self.session.add(event)

    async def get_events(
        self, page: int, page_size: int, date_from: date | None = None
    ) -> list[Event]:
        query = select(Event).options(selectinload(Event.place))
        query = query.order_by(Event.event_time, Event.id)

        if date_from is not None:
            query = query.where(Event.event_time >= date_from)

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        results = await self.session.execute(query)
        return results.scalars().all()

    async def count_events(self, date_from: date | None = None) -> int:

        query = select(func.count()).select_from(Event)
        if date_from is not None:
            query = query.where(Event.event_time >= date_from)
        res = await self.session.execute(query)
        counts = res.scalar_one()
        return counts

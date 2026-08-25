from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from events_aggregator.models import Place


class PlaceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_place_by_id(self, place_id: UUID) -> Place | None:
        place = await self.session.get(Place, place_id)
        return place

    def add_place(self, place: Place):
        self.session.add(place)

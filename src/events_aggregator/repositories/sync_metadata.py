from sqlalchemy.ext.asyncio import AsyncSession

from events_aggregator.models import SyncMetadata


class SyncMetadataRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_metadata(self) -> SyncMetadata | None:
        data = await self.session.get(SyncMetadata, 1)
        return data

    def add_metadata(self, metadata: SyncMetadata) -> None:
        self.session.add(metadata)

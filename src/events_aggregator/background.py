import asyncio
import logging

import httpx

from events_aggregator.clients.events_provider import EventsProviderClient
from events_aggregator.db.session import async_session_maker
from events_aggregator.repositories.event import EventRepository
from events_aggregator.repositories.place import PlaceRepository
from events_aggregator.repositories.sync_metadata import SyncMetadataRepository
from events_aggregator.services.sync import SyncService

DAY_SECONDS = 60 * 60 * 24

logger = logging.getLogger(__name__)


async def run_daily_sync(client: EventsProviderClient):
    while True:
        try:
            async with async_session_maker() as session:
                event_repository = EventRepository(session)
                place_repository = PlaceRepository(session)
                sync_metadata_repository = SyncMetadataRepository(session)

                sync_service = SyncService(
                    session=session,
                    client=client,
                    event_repository=event_repository,
                    place_repository=place_repository,
                    sync_metadata_repository=sync_metadata_repository,
                )
                await sync_service.sync_events()
        except httpx.RequestError as exc:
            logger.error("Ошибка фоновой синхронизации: %s", exc)

        await asyncio.sleep(DAY_SECONDS)

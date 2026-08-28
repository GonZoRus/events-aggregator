import asyncio

from events_aggregator.clients.events_provider import EventsProviderClient
from events_aggregator.config import EVENTS_PROVIDER_API_KEY, EVENTS_PROVIDER_BASE_URL
from events_aggregator.db.session import async_session_maker
from events_aggregator.repositories.event import EventRepository
from events_aggregator.repositories.place import PlaceRepository
from events_aggregator.repositories.sync_metadata import SyncMetadataRepository
from events_aggregator.services.sync import SyncService

DAY_SECONDS = 10


async def run_daily_sync():
    while True:
        async with async_session_maker() as session:
            event_repository = EventRepository(session)
            place_repository = PlaceRepository(session)
            sync_metadata_repository = SyncMetadataRepository(session)
            client = EventsProviderClient(
                EVENTS_PROVIDER_BASE_URL, EVENTS_PROVIDER_API_KEY
            )
            sync_service = SyncService(
                session=session,
                client=client,
                event_repository=event_repository,
                place_repository=place_repository,
                sync_metadata_repository=sync_metadata_repository,
            )
            await sync_service.sync_events()

        await asyncio.sleep(DAY_SECONDS)

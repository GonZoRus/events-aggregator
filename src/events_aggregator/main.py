from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from events_aggregator.clients.events_provider import EventsProviderClient
from events_aggregator.config import EVENTS_PROVIDER_API_KEY, EVENTS_PROVIDER_BASE_URL
from events_aggregator.db.session import get_session
from events_aggregator.repositories.event import EventRepository
from events_aggregator.repositories.place import PlaceRepository
from events_aggregator.repositories.sync_metadata import SyncMetadataRepository
from events_aggregator.services.sync import SyncService

app = FastAPI()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/sync/trigger")
async def trigger_sync(session: Annotated[AsyncSession, Depends(get_session)]):
    event_repository = EventRepository(session)
    place_repository = PlaceRepository(session)
    sync_metadata_repository = SyncMetadataRepository(session)
    client = EventsProviderClient(EVENTS_PROVIDER_BASE_URL, EVENTS_PROVIDER_API_KEY)
    sync_service = SyncService(
        session=session,
        client=client,
        event_repository=event_repository,
        place_repository=place_repository,
        sync_metadata_repository=sync_metadata_repository)
    await sync_service.sync_events()
    return {"status": "ok"}
from datetime import date
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from events_aggregator.clients.events_provider import EventsProviderClient
from events_aggregator.config import EVENTS_PROVIDER_API_KEY, EVENTS_PROVIDER_BASE_URL
from events_aggregator.db.session import get_session
from events_aggregator.repositories.event import EventRepository
from events_aggregator.repositories.place import PlaceRepository
from events_aggregator.repositories.sync_metadata import SyncMetadataRepository
from events_aggregator.schemas.events import EventResponse, EventsResponse
from events_aggregator.services.sync import SyncService

app = FastAPI()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/sync/trigger", tags=["Ручная синхронизация"])
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
        sync_metadata_repository=sync_metadata_repository,
    )
    await sync_service.sync_events()
    return {"status": "ok"}


@app.get(
    "/api/events", tags=["Получение списка событий"], response_model=EventsResponse
)
async def get_events(
    session: Annotated[AsyncSession, Depends(get_session)],
    date_from: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
):

    event_repository = EventRepository(session)
    count = await event_repository.count_events(date_from=date_from)
    events = await event_repository.get_events(
        page=page, page_size=page_size, date_from=date_from
    )
    total_pages = (count + page_size - 1) // page_size
    if count > 0 and page > total_pages:
        raise HTTPException(status_code=404, detail="Страница не найдена")

    result = [EventResponse.model_validate(event) for event in events]

    next_page = page + 1
    if next_page > total_pages:
        next_page = None

    previous_page = page - 1
    if previous_page < 1:
        previous_page = None

    if next_page:
        if date_from is None:
            next_url = f"/api/events/?page={next_page}&page_size={page_size}"
        else:
            next_url = f"/api/events/?date_from={date_from}&page={next_page}&page_size={page_size}"
    else:
        next_url = None

    if previous_page:
        if date_from is None:
            previous_url = f"/api/events/?page={previous_page}&page_size={page_size}"
        else:
            previous_url = f"/api/events/?date_from={date_from}&page={previous_page}&page_size={page_size}"
    else:
        previous_url = None

    events_response = EventsResponse(
        count=count, next=next_url, previous=previous_url, results=result
    )

    return events_response

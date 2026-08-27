import uuid
from datetime import date
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from events_aggregator.cache import get_cached_seats, save_cached_seats
from events_aggregator.clients.events_provider import EventsProviderClient
from events_aggregator.config import EVENTS_PROVIDER_API_KEY, EVENTS_PROVIDER_BASE_URL
from events_aggregator.db.session import get_session
from events_aggregator.repositories.event import EventRepository
from events_aggregator.repositories.place import PlaceRepository
from events_aggregator.repositories.sync_metadata import SyncMetadataRepository
from events_aggregator.repositories.ticket import TicketRepository
from events_aggregator.schemas.event_details import EventDetails
from events_aggregator.schemas.events import EventResponse, EventsResponse
from events_aggregator.schemas.seats import SeatsResponse
from events_aggregator.schemas.tickets import TicketPost, TicketResponse
from events_aggregator.services.creat_tiket import CreateTicketUsecase
from events_aggregator.services.exceptions import (
    EventNotFound,
    ProviderUnavailable,
    SeatAlreadyTaken,
)
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


@app.get(
    "/api/events/{event_id}",
    tags=["Получение деталей события"],
    response_model=EventDetails,
)
async def get_event_details(
        session: Annotated[AsyncSession, Depends(get_session)],
        event_id: uuid.UUID,
) -> EventDetails:
    event_repository = EventRepository(session)
    res = await event_repository.get_event_with_place_by_id(event_id)
    if res is None:
        raise HTTPException(status_code=404, detail="Событие с таким id не найдено")
    return EventDetails.model_validate(res)


@app.get(
    "/api/events/{event_id}/seats",
    tags=["Получение информации о местах"],
    response_model=SeatsResponse,
)
async def get_seats(event_id: uuid.UUID) -> SeatsResponse:
    cached = get_cached_seats(event_id)
    if cached is not None:
        res = SeatsResponse(
            event_id=event_id,
            available_seats=cached["seats"],
        )
        return res

    client = EventsProviderClient(EVENTS_PROVIDER_BASE_URL, EVENTS_PROVIDER_API_KEY)
    seats = await client.seats(event_id)

    result = SeatsResponse(
        event_id=event_id,
        available_seats=seats,
    )
    save_cached_seats(seats, event_id)
    return result


@app.post(
    '/api/tickets', tags=["Регистрация на событие"],
    status_code=201,
    response_model=TicketResponse)
async def create_ticket(
        session: Annotated[AsyncSession, Depends(get_session)],
        data: TicketPost) -> TicketResponse:
    ticket_repository = TicketRepository(session)
    client = EventsProviderClient(EVENTS_PROVIDER_BASE_URL, EVENTS_PROVIDER_API_KEY)
    create_ticket_usecase = CreateTicketUsecase(
        client=client,
        ticket_repository=ticket_repository
    )
    try:

        ticket_id = await create_ticket_usecase.execute(
            event_id=data.event_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            seat=data.seat)
    except SeatAlreadyTaken:
        raise HTTPException(
            status_code=400,
            detail="Место уже занято"
        )
    except EventNotFound:
        raise HTTPException(
            status_code=404,
            detail="Событие с указанным ID не найдено."
        )
    except ProviderUnavailable:
        raise HTTPException(
            status_code=502,
            detail='Ошибка внешнего сервиса'
        )

    return TicketResponse(
        ticket_id=ticket_id
    )

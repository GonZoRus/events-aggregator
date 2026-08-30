import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated
from urllib.parse import urlencode, urljoin

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from events_aggregator.background import run_daily_sync
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
from events_aggregator.services.create_ticket import CreateTicketUsecase
from events_aggregator.services.delete_ticket import DeleteTicketUsecase
from events_aggregator.services.events import EventsService
from events_aggregator.services.exceptions import (
    EventNotFound,
    ProviderUnavailable,
    SeatAlreadyTaken,
    TicketNotFound,
)
from events_aggregator.services.sync import SyncService


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_daily_sync())

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


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
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    date_from: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
):
    events_url = urljoin(str(request.base_url), "/api/events/")
    event_service = EventsService()
    event_repository = EventRepository(session)
    count = await event_repository.count_events(date_from=date_from)
    events = await event_repository.get_events(
        page=page, page_size=page_size, date_from=date_from
    )

    total_pages = event_service.get_total_pages(count, page_size)

    if not event_service.is_page_valid(page=page, total_pages=total_pages, count=count):
        raise HTTPException(status_code=404, detail="Страница не найдена")

    result = [EventResponse.model_validate(event) for event in events]

    next_page = event_service.get_next_page(page, total_pages)
    previous_page = event_service.get_previous_page(page)

    if next_page:
        params = {
            "page": next_page,
            "page_size": page_size,
        }
        if date_from is not None:
            params["date_from"] = date_from

        next_url = events_url + "?" + urlencode(params)
    else:
        next_url = None

    if previous_page:
        params = {
            "page": previous_page,
            "page_size": page_size,
        }
        if date_from is not None:
            params["date_from"] = date_from

        previous_url = events_url + "?" + urlencode(params)
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
    try:
        seats = await client.seats(event_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Событие не найдено")
        raise HTTPException(status_code=502, detail="Ошибка внешнего сервиса")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Внешний сервис не доступен")

    result = SeatsResponse(
        event_id=event_id,
        available_seats=seats,
    )
    save_cached_seats(seats, event_id)
    return result


@app.post(
    "/api/tickets",
    tags=["Регистрация на событие"],
    status_code=201,
    response_model=TicketResponse,
)
async def create_ticket(
    session: Annotated[AsyncSession, Depends(get_session)], data: TicketPost
) -> TicketResponse:
    ticket_repository = TicketRepository(session)
    client = EventsProviderClient(EVENTS_PROVIDER_BASE_URL, EVENTS_PROVIDER_API_KEY)
    create_ticket_usecase = CreateTicketUsecase(
        client=client, ticket_repository=ticket_repository
    )
    try:
        ticket_id = await create_ticket_usecase.execute(
            event_id=data.event_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            seat=data.seat,
        )
    except SeatAlreadyTaken:
        raise HTTPException(status_code=400, detail="Место уже занято")
    except EventNotFound:
        raise HTTPException(
            status_code=404, detail="Событие с указанным ID не найдено."
        )
    except ProviderUnavailable:
        raise HTTPException(status_code=502, detail="Ошибка внешнего сервиса")

    return TicketResponse(ticket_id=ticket_id)


@app.delete("/api/tickets/{ticket_id}", tags=["Отмена регистрации"], status_code=200)
async def delete_ticket(
    ticket_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_session)]
):
    ticket_repository = TicketRepository(session)
    client = EventsProviderClient(EVENTS_PROVIDER_BASE_URL, EVENTS_PROVIDER_API_KEY)
    delete_ticket_usecase = DeleteTicketUsecase(
        client=client, ticket_repository=ticket_repository
    )
    try:
        await delete_ticket_usecase.execute(ticket_id)
    except TicketNotFound:
        raise HTTPException(status_code=404, detail="Билет не найден")
    except ProviderUnavailable:
        raise HTTPException(status_code=502, detail="Ошибка внешнего сервиса")
    return {"success": True}

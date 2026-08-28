from unittest.mock import AsyncMock, Mock, call

import pytest

from events_aggregator.clients.events_provider import (
    EventsPaginator,
    EventsProviderClient,
)
from events_aggregator.schemas.provider import ProviderEventsResponse


def make_event(event_id: str, name: str) -> dict:
    return {
        "id": event_id,
        "name": name,
        "place": {
            "id": "660e8400-e29b-41d4-a716-446655440000",
            "name": "Test place",
            "city": "Moscow",
            "address": "Test address",
            "seats_pattern": "A1-100",
            "changed_at": "2026-01-01T10:00:00+03:00",
            "created_at": "2025-12-01T10:00:00+03:00",
        },
        "event_time": "2026-01-11T17:00:00+03:00",
        "registration_deadline": "2026-01-10T17:00:00+03:00",
        "status": "published",
        "number_of_visitors": 5,
        "changed_at": "2026-01-01T10:00:00+03:00",
        "created_at": "2025-12-01T10:00:00+03:00",
        "status_changed_at": "2026-01-01T10:00:00+03:00",
    }


test_page = ProviderEventsResponse.model_validate(
    {
        "next": None,
        "previous": None,
        "results": [
            make_event(
                "550e8400-e29b-41d4-a716-446655440000",
                "Конференция по Python",
            ),
            make_event(
                "550e8400-e29b-41d4-a716-446655440001",
                "Разбор ошибок",
            ),
        ],
    }
)

first_page = ProviderEventsResponse.model_validate(
    {
        "next": "pages2",
        "previous": None,
        "results": [
            make_event(
                "550e8400-e29b-41d4-a716-446655440002",
                "Жарим пирожки",
            )
        ],
    }
)

second_page = ProviderEventsResponse.model_validate(
    {
        "next": None,
        "previous": "pages1",
        "results": [
            make_event(
                "550e8400-e29b-41d4-a716-446655440003",
                "Конференция по собачкам",
            )
        ],
    }
)

empty_middle_page = ProviderEventsResponse.model_validate(
    {
        "next": "pages3",
        "previous": "pages1",
        "results": [],
    }
)

third_page = ProviderEventsResponse.model_validate(
    {
        "next": None,
        "previous": "pages2",
        "results": [
            make_event(
                "550e8400-e29b-41d4-a716-446655440004",
                "Конференция по кошкам",
            )
        ],
    }
)


@pytest.mark.asyncio
async def test_paginator():
    fake_client = Mock(spec=EventsProviderClient)
    fake_client.events = AsyncMock(return_value=test_page)

    paginator = EventsPaginator(fake_client, date="2026-01-05")

    events = []
    async for event in paginator:
        events.append(event)

    assert events == test_page.results
    fake_client.events.assert_awaited_once_with("2026-01-05")


@pytest.mark.asyncio
async def test_paginator_with_two_pages():
    fake_client = Mock(spec=EventsProviderClient)
    fake_client.events = AsyncMock(return_value=first_page)
    fake_client.get_page = AsyncMock(return_value=second_page)

    paginator = EventsPaginator(fake_client, date="2026-01-05")

    events = []
    async for event in paginator:
        events.append(event)

    assert events == first_page.results + second_page.results

    fake_client.events.assert_awaited_once_with("2026-01-05")
    fake_client.get_page.assert_awaited_once_with("pages2")


@pytest.mark.asyncio
async def test_paginator_skips_empty_page():
    fake_client = Mock(spec=EventsProviderClient)
    fake_client.events = AsyncMock(return_value=first_page)
    fake_client.get_page = AsyncMock(
        side_effect=[
            empty_middle_page,
            third_page,
        ]
    )

    paginator = EventsPaginator(fake_client, date="2026-01-05")

    events = []
    async for event in paginator:
        events.append(event)

    assert events == first_page.results + third_page.results

    fake_client.events.assert_awaited_once_with("2026-01-05")
    fake_client.get_page.assert_has_awaits(
        [
            call("pages2"),
            call("pages3"),
        ],
        any_order=False,
    )

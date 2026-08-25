from unittest.mock import AsyncMock, Mock, call

import pytest

from events_aggregator.clients.events_provider import (
    EventsPaginator,
    EventsProviderClient,
)

test_dict = {
    "next": None,
    "previous": None,
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "name": "Конференция по Python"},
        {"id": "550e8400-e29b-41d4-a716-4466554400321", "name": "Разбор ошибок"},
    ],
}

first_pages = {
    "next": "pages2",
    "results": [
        {"id": "550e8420-e39b-41d4-a716-4426554400321", "name": "Жарим пирожки"}
    ],
}

second_pages = {
    "next": None,
    "results": [
        {
            "id": "550e8420-e39b-41d4-a716-4426551400321",
            "name": "Конференция по Собачкам",
        }
    ],
}

empty_middle_page = {"next": "pages3", "results": []}

third_pages = {
    "next": None,
    "results": [
        {"id": "550e8420-e39b-41d4-a716-4426551400321", "name": "Конференция по кошка"}
    ],
}


@pytest.mark.asyncio
async def test_paginator():
    fake_client = Mock(spec=EventsProviderClient)
    fake_client.events = AsyncMock(return_value=test_dict)

    paginator = EventsPaginator(fake_client, date="2026-01-05")
    events = []
    async for event in paginator:
        events.append(event)

    assert events == test_dict["results"]
    fake_client.events.assert_awaited_once_with("2026-01-05")


@pytest.mark.asyncio
async def test_paginator_with_two_pages():
    fake_client = Mock(spec=EventsProviderClient)
    fake_client.events = AsyncMock(return_value=first_pages)
    fake_client.get_page = AsyncMock(return_value=second_pages)
    paginator = EventsPaginator(fake_client, date="2026-01-05")
    events = []
    async for event in paginator:
        events.append(event)

    assert events == first_pages["results"] + second_pages["results"]
    fake_client.events.assert_awaited_once_with("2026-01-05")
    fake_client.get_page.assert_awaited_once_with("pages2")


@pytest.mark.asyncio
async def test_paginator_skips_empty_page():
    fake_client = Mock(spec=EventsProviderClient)
    fake_client.events = AsyncMock(return_value=first_pages)
    fake_client.get_page = AsyncMock(side_effect=[empty_middle_page, third_pages])
    paginator = EventsPaginator(fake_client, date="2026-01-05")
    events = []
    async for event in paginator:
        events.append(event)

    assert (
        events
        == first_pages["results"]
        + empty_middle_page["results"]
        + third_pages["results"]
    )
    fake_client.events.assert_awaited_once_with("2026-01-05")
    fake_client.get_page.assert_has_awaits(
        [call("pages2"), call("pages3")], any_order=False
    )

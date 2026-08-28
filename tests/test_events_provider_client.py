from unittest.mock import AsyncMock, Mock, patch

import pytest

from events_aggregator.clients.events_provider import EventsProviderClient


def test_provider_client():
    with patch(
        "events_aggregator.clients.events_provider.httpx.AsyncClient"
    ) as fake_client:
        EventsProviderClient(base_url="http://example.com", api_key="fake_key")
        fake_client.assert_called_once_with(
            base_url="http://example.com", headers={"x-api-key": "fake_key"},
            follow_redirects=True)


@pytest.mark.asyncio
async def test_events_returns_json_and_calls_provider():
    with patch(
        "events_aggregator.clients.events_provider.httpx.AsyncClient"
    ) as fake_client:
        client = EventsProviderClient(
            base_url="http://example.com",
            api_key="fake_key",
        )

        mock_http_client = fake_client.return_value
        fake_response = Mock()
        mock_http_client.get = AsyncMock(return_value=fake_response)

        fake_json = {
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Test event",
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
            ],
        }

        fake_response.json.return_value = fake_json

        result = await client.events(date="2020-04-01")

        fake_response.raise_for_status.assert_called_once_with()

        assert result.next is None
        assert result.previous is None
        assert len(result.results) == 1
        assert result.results[0].name == "Test event"

        mock_http_client.get.assert_awaited_once_with(
            "/api/events/",
            params={"changed_at": "2020-04-01"},
        )

        fake_client.assert_called_once_with(
            base_url="http://example.com",
            headers={"x-api-key": "fake_key"},
            follow_redirects=True,
        )


@pytest.mark.asyncio
async def test_get_page():
    with patch(
        "events_aggregator.clients.events_provider.httpx.AsyncClient"
    ) as fake_client:
        client = EventsProviderClient(
            base_url="http://example.com",
            api_key="fake_key",
        )

        mock_http_client = fake_client.return_value
        fake_response = Mock()
        mock_http_client.get = AsyncMock(return_value=fake_response)

        fake_json = {
            "next": "http://example_next.com",
            "previous": None,
            "results": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Test event",
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
            ],
        }

        next_url = "http://example_next.com"
        fake_response.json.return_value = fake_json

        result = await client.get_page(next_url)

        fake_response.raise_for_status.assert_called_once_with()

        assert result.next == "http://example_next.com"
        assert result.previous is None
        assert len(result.results) == 1
        assert result.results[0].name == "Test event"

        mock_http_client.get.assert_awaited_once_with(next_url)


@pytest.mark.asyncio
async def test_seats_returns_list_and_calls_provider():
    with patch(
        "events_aggregator.clients.events_provider.httpx.AsyncClient"
    ) as fake_client:
        client = EventsProviderClient(base_url="http://example.com", api_key="fake_key")
        mock_http_client = fake_client.return_value
        fake_response = Mock()
        mock_http_client.get = AsyncMock(return_value=fake_response)
        fake_json = {"seats": ["A1", "A3", "A4"]}
        fake_response.json.return_value = fake_json
        result = await client.seats(event_id="event-uuid")
        fake_response.raise_for_status.assert_called_once_with()
        assert result == fake_json["seats"]
        mock_http_client.get.assert_awaited_once_with("/api/events/event-uuid/seats/")


@pytest.mark.asyncio
async def test_register_returns_string_and_calls_provider():
    with patch(
        "events_aggregator.clients.events_provider.httpx.AsyncClient"
    ) as fake_client:
        client = EventsProviderClient(base_url="http://example.com", api_key="fake_key")
        mock_http_client = fake_client.return_value
        fake_response = Mock()
        mock_http_client.post = AsyncMock(return_value=fake_response)

        fake_json = {"ticket_id": "4baef786-4578-432e-9927-7f721d1c0be2"}
        fake_body = {
            "first_name": "Иван",
            "last_name": "Иванов",
            "seat": "A20",
            "email": "ivan@example.com",
        }
        fake_response.json.return_value = fake_json
        result = await client.register(event_id="event-uuid", **fake_body)
        assert result == fake_json["ticket_id"]
        fake_response.raise_for_status.assert_called_once_with()
        mock_http_client.post.assert_awaited_once_with(
            "/api/events/event-uuid/register/", json=fake_body
        )


@pytest.mark.asyncio
async def test_unregister_returns_string_and_calls_provider():
    with patch(
        "events_aggregator.clients.events_provider.httpx.AsyncClient"
    ) as fake_client:
        client = EventsProviderClient(base_url="http://example.com", api_key="fake_key")
        mock_http_client = fake_client.return_value
        fake_response = Mock()
        mock_http_client.request = AsyncMock(return_value=fake_response)

        fake_json = {"success": True}
        fake_body = {"ticket_id": "1fed0122-b675-42e2-8ae7-49bfb53e8d7f"}
        fake_response.json.return_value = fake_json
        result = await client.unregister(
            event_id="event-uuid", ticket_id="1fed0122-b675-42e2-8ae7-49bfb53e8d7f"
        )
        assert result == fake_json
        fake_response.raise_for_status.assert_called_once_with()
        mock_http_client.request.assert_awaited_once_with(
            "DELETE", "/api/events/event-uuid/unregister/", json=fake_body
        )

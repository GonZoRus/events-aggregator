from unittest.mock import AsyncMock, Mock, patch
from events_aggregator.clients.events_provider import EventsProviderClient
import pytest


def test_provider_client():
	with patch("events_aggregator.clients.events_provider.httpx.AsyncClient") as fake_client:
		EventsProviderClient(base_url="http://example.com", api_key="fake_key")
		fake_client.assert_called_once_with(base_url="http://example.com",
		                                    headers={"x-api-key": "fake_key"})


@pytest.mark.asyncio
async def test_provider_client_async():
	with patch("events_aggregator.clients.events_provider.httpx.AsyncClient") as fake_client:
		client = EventsProviderClient(base_url="http://example.com", api_key="fake_key")

		mock_http_client = fake_client.return_value
		fake_response = Mock()
		mock_http_client.get = AsyncMock(return_value=fake_response)
		fake_json = {
			"next": None,
			"results": [{"id": "1", "name": "Test event"}],
		}
		fake_response.json.return_value = fake_json

		result = await client.events(date="2020-04-01")
		fake_response.raise_for_status.assert_called_once_with()
		assert result == fake_json
		mock_http_client.get.assert_awaited_once_with(
			"/api/events/",
			params={"changed_at": "2020-04-01"},
		)
		fake_client.assert_called_once_with(base_url="http://example.com",
		                                    headers={"x-api-key": "fake_key"})

import uuid
from collections import deque

import httpx

from events_aggregator.schemas.provider import ProviderEventsResponse


class EventsProviderClient:
    def __init__(self, base_url: str, api_key: str):
        self.client = httpx.AsyncClient(
            base_url=base_url, headers={"x-api-key": api_key}, follow_redirects=True
        )

    async def events(self, date: str) -> ProviderEventsResponse:
        response = await self.client.get("/api/events/", params={"changed_at": date})
        response.raise_for_status()
        return ProviderEventsResponse.model_validate(response.json())

    async def get_page(self, url: str) -> ProviderEventsResponse:
        response = await self.client.get(url)
        response.raise_for_status()
        return ProviderEventsResponse.model_validate(response.json())

    async def seats(self, event_id: uuid.UUID) -> list[str]:
        response = await self.client.get(f"/api/events/{event_id}/seats/")
        response.raise_for_status()
        available_seats = response.json()["seats"]
        return available_seats

    async def register(
        self, event_id: str, first_name: str, last_name: str, email: str, seat: str
    ) -> str:
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "seat": seat,
        }
        response = await self.client.post(
            f"/api/events/{event_id}/register/", json=data
        )
        response.raise_for_status()
        ticket_id = response.json()["ticket_id"]
        return ticket_id

    async def unregister(self, event_id: str, ticket_id: str) -> dict:
        body = {"ticket_id": ticket_id}
        response = await self.client.request(
            "DELETE",
            f"/api/events/{event_id}/unregister/",
            json=body,
        )
        response.raise_for_status()
        return response.json()


class EventsPaginator:
    def __init__(self, client: EventsProviderClient, date):
        self.client = client
        self.date = date
        self.current_events = deque()
        self.next_url = None
        self.started = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            if not self.started:
                first_event = await self.client.events(self.date)
                self.next_url = first_event.next
                self.current_events.extend(first_event.results)
                self.started = True

            if self.current_events:
                return self.current_events.popleft()

            if not self.next_url:
                raise StopAsyncIteration

            next_events = await self.client.get_page(self.next_url)
            self.next_url = next_events.next
            self.current_events.extend(next_events.results)

import httpx

from events_aggregator import cache
from events_aggregator.clients.events_provider import EventsProviderClient
from events_aggregator.services.exceptions import EventNotFound, ProviderUnavailable


class SeatsService:
    def __init__(self, client: EventsProviderClient):
        self.client = client

    async def get_seats(self, event_id):
        caches = cache.get_cached_seats(event_id)
        if caches is not None:
            return caches["seats"]
        try:
            seats = await self.client.seats(event_id)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise EventNotFound()
            raise ProviderUnavailable()

        except httpx.RequestError:
            raise ProviderUnavailable()

        cache.save_cached_seats(seats, event_id)
        return seats

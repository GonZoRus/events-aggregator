import httpx
from collections import deque


class EventsProviderClient:
	def __init__(self, base_url: str, api_key: str):
		self.client = httpx.AsyncClient(base_url=base_url, headers={"x-api-key": api_key})

	async def events(self, date: str) -> dict:
		response = await self.client.get("/api/events/", params={"changed_at": date})
		response.raise_for_status()
		return response.json()

	async def get_page(self, url: str) -> dict:
		response = await self.client.get(url)
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
				self.next_url = first_event["next"]
				self.current_events.extend(first_event["results"])
				self.started = True

			if self.current_events:
				return self.current_events.popleft()

			if not self.next_url:
				raise StopAsyncIteration

			next_events = await self.client.get_page(self.next_url)
			self.next_url = next_events["next"]
			self.current_events.extend(next_events["results"])

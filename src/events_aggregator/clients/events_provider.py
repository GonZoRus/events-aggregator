import httpx


class EventsProviderClient:
	def __init__(self, base_url:str, api_key:str):
		self.client = httpx.AsyncClient(base_url=base_url, headers={"x-api-key": api_key})

	async def events(self,date: str)-> dict:
		response = await self.client.get("/api/events/", params={"changed_at": date})
		response.raise_for_status()
		return response.json()

	async def get_page(self,url:str)-> dict:
		response = await self.client.get(url)
		response.raise_for_status()
		return response.json()

class EventsPaginator:
	def __init__(self, client:EventsProviderClient, date):
		self.client = client
		self.date = date
		self.current_events = []
		self.next_url = None
		self.started = False

	def  __aiter__(self):
		return self

	async def __anext__(self):
		if not self.started:

			first_event = await self.client.events(self.date)
			self.next_url = first_event["next"]
			for event in first_event["results"]:
				self.current_events.append(event)

			self.started = True
import datetime

from events_aggregator.repositories.event import EventRepository
from events_aggregator.services.exceptions import PageNotFound


class EventsService:
    def __init__(self, repository: EventRepository):
        self.repository = repository

    def get_total_pages(self, count: int, page_size: int) -> int:
        return (count + page_size - 1) // page_size

    def get_next_page(self, page: int, total_pages: int) -> int | None:
        next_page = page + 1
        if next_page > total_pages:
            return None
        return next_page

    def get_previous_page(self, page: int) -> int | None:
        previous_page = page - 1
        if previous_page < 1:
            return None
        return previous_page

    def is_page_valid(self, page: int, total_pages: int, count: int) -> bool:
        return not (count > 0 and page > total_pages)

    async def get_the_event_page(
        self, page: int, page_size: int, date_from: datetime.date | None = None
    ):
        count = await self.repository.count_events(date_from=date_from)
        total_pages = self.get_total_pages(count, page_size)

        if not self.is_page_valid(page=page, total_pages=total_pages, count=count):
            raise PageNotFound()

        events = await self.repository.get_events(
            page=page, page_size=page_size, date_from=date_from
        )

        next_page = self.get_next_page(page, total_pages)
        previous_page = self.get_previous_page(page)

        return count, events, next_page, previous_page

class EventsService:
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

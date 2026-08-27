import time
import uuid

seats_cache = {}


def save_cached_seats(seats: list[str], event_id: uuid.UUID):
    seats_cache[event_id] = {"seats": seats, "saved_at": time.monotonic()}


def get_cached_seats(event_id: uuid.UUID):
    if event_id in seats_cache:
        elapsed = time.monotonic() - seats_cache[event_id]["saved_at"]
        if elapsed >= 30:
            seats_cache.pop(event_id)
            return None
        return seats_cache[event_id]

    return None

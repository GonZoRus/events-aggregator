from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from events_aggregator.clients.events_provider import (
    EventsPaginator,
    EventsProviderClient,
)
from events_aggregator.models.event import Event
from events_aggregator.models.place import Place
from events_aggregator.models.syncmetadata import SyncMetadata, SyncStatus
from events_aggregator.repositories.event import EventRepository
from events_aggregator.repositories.place import PlaceRepository
from events_aggregator.repositories.sync_metadata import SyncMetadataRepository


class SyncService:
    def __init__(
        self,
        session: AsyncSession,
        client: EventsProviderClient,
        event_repository: EventRepository,
        place_repository: PlaceRepository,
        sync_metadata_repository: SyncMetadataRepository,
    ):

        self.session = session
        self.client = client
        self.event_repository = event_repository
        self.place_repository = place_repository
        self.sync_metadata_repository = sync_metadata_repository

    async def sync_events(self):

        sync_metadata = await self.sync_metadata_repository.get_metadata()

        if sync_metadata is None:
            new_metadata = SyncMetadata(
                id=1,
                last_sync_time=datetime.now(UTC),
                last_changed_at=datetime(2000, 1, 1, tzinfo=UTC),
                sync_status=SyncStatus.RUNNING,
            )
            page = EventsPaginator(self.client, date="2000-01-01")
            self.sync_metadata_repository.add_metadata(new_metadata)
            sync_metadata = new_metadata
        else:
            sync_date = sync_metadata.last_changed_at.date().isoformat()
            page = EventsPaginator(self.client, date=sync_date)
            sync_metadata.sync_status = SyncStatus.RUNNING

        await self.session.commit()

        try:
            latest_changed_at = None
            async for provider_event in page:
                if (
                    latest_changed_at is None
                    or provider_event.changed_at > latest_changed_at
                ):
                    latest_changed_at = provider_event.changed_at

                db_place = await self.place_repository.get_place_by_id(
                    provider_event.place.id
                )

                if db_place is None:
                    new_place = Place(
                        id=provider_event.place.id,
                        name=provider_event.place.name,
                        city=provider_event.place.city,
                        address=provider_event.place.address,
                        seats_pattern=provider_event.place.seats_pattern,
                    )
                    self.place_repository.add_place(new_place)
                else:
                    db_place.name = provider_event.place.name
                    db_place.city = provider_event.place.city
                    db_place.address = provider_event.place.address
                    db_place.seats_pattern = provider_event.place.seats_pattern

                db_event = await self.event_repository.get_event_by_id(
                    provider_event.id
                )

                if db_event is None:
                    new_event = Event(
                        id=provider_event.id,
                        place_id=provider_event.place.id,
                        name=provider_event.name,
                        event_time=provider_event.event_time,
                        registration_deadline=provider_event.registration_deadline,
                        status=provider_event.status,
                        number_of_visitors=provider_event.number_of_visitors,
                    )

                    self.event_repository.add_event(new_event)
                else:
                    db_event.place_id = provider_event.place.id
                    db_event.name = provider_event.name
                    db_event.event_time = provider_event.event_time
                    db_event.registration_deadline = (
                        provider_event.registration_deadline
                    )
                    db_event.status = provider_event.status
                    db_event.number_of_visitors = provider_event.number_of_visitors

            sync_metadata.last_sync_time = datetime.now(UTC)
            sync_metadata.sync_status = SyncStatus.SUCCESS
            if latest_changed_at is not None:
                sync_metadata.last_changed_at = latest_changed_at

            await self.session.commit()
        except Exception:
            await self.session.rollback()

            sync_metadata.sync_status = SyncStatus.FAILED
            sync_metadata.last_sync_time = datetime.now(UTC)
            await self.session.commit()
            raise

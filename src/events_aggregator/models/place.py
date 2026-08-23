from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from events_aggregator.db.base import Base


class Place(Base):
    __tablename__ = 'places'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    city: Mapped[str] = mapped_column()
    address: Mapped[str] = mapped_column()
    seats_pattern: Mapped[str] = mapped_column()

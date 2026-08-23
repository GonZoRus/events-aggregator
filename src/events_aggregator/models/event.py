import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from events_aggregator.db.base import Base


class Event(Base):
    __tablename__ = "events"

    place = relationship("Place")

    id: Mapped[UUID] = mapped_column(primary_key=True)
    place_id: Mapped[UUID] = mapped_column(ForeignKey("places.id"))
    name: Mapped[str] = mapped_column()
    event_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    registration_deadline: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column()
    number_of_visitors: Mapped[int] = mapped_column()

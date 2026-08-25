import datetime
from enum import Enum

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from events_aggregator.db.base import Base


class SyncStatus(Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class SyncMetadata(Base):
    __tablename__ = "sync_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    last_sync_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    last_changed_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[SyncStatus] = mapped_column(
        SQLEnum(
            SyncStatus,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        )
    )

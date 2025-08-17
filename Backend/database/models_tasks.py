# database/models_tasks.py
from __future__ import annotations
from datetime import datetime, date, timezone
from sqlalchemy import (
    Integer, String, DateTime, Date, Text, ForeignKey, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from database.db import Base, async_session

# ──────────────────────────────────────────────────────────
# Batch = "TaskGroup"
# ──────────────────────────────────────────────────────────
class TaskGroup(Base):
    __tablename__ = "task_groups"

    id:       Mapped[int]       = mapped_column(primary_key=True)
    username: Mapped[str]       = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    status:   Mapped[str]       = mapped_column(String(100), default="queued")

    items: Mapped[list["TaskItem"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )

    # handy aggregate view
    @hybrid_property
    def percent_done(self) -> float:
        if not self.items:
            return 0.0
        done = sum(1 for i in self.items if i.status == "SUCCESS")
        return done / len(self.items) * 100


# ──────────────────────────────────────────────────────────
# Item base – one row per unit of work
# ──────────────────────────────────────────────────────────
class TaskItem(Base):
    __tablename__ = "task_items"

    id:            Mapped[int] = mapped_column(primary_key=True)
    group_id:      Mapped[int] = mapped_column(ForeignKey("task_groups.id"))
    type:          Mapped[str] = mapped_column(String(50))      # discriminator
    status:        Mapped[str] = mapped_column(String(30), default="PENDING")
    queued_at:     Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    started_at:    Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at:   Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    celery_uuid:   Mapped[str | None] = mapped_column(String(50))
    # optional generic payload for small, throw-away data
    payload:       Mapped[dict] = mapped_column(JSON, default=dict)

    group: Mapped["TaskGroup"] = relationship(back_populates="items")

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "base",
    }


# ──────────────────────────────────────────────────────────
# Flavour 1 – SSV site tasks
# ──────────────────────────────────────────────────────────
class SSVTask(TaskItem):
    __tablename__ = "ssv_task_items"
    id: Mapped[int] = mapped_column(
        ForeignKey("task_items.id"), primary_key=True
    )

    site_id:   Mapped[str]  = mapped_column(String(100))
    site_date: Mapped[date] = mapped_column(Date)
    tech:   Mapped[str]  = mapped_column(String(100), default="LTE")

    __mapper_args__ = {"polymorphic_identity": "ssv"}



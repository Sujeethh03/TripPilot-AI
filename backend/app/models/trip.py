"""Trip model (PROJECT_PLAN §10).

The itinerary is stored as JSONB — a deliberate denormalization (§5.6 #2) for
read speed; its shape is validated by the Pydantic Itinerary SSOT at the app
boundary.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint("budget_inr > 0", name="budget_positive"),
        CheckConstraint("start_date <= end_date", name="dates_ordered"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(255))
    destination: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[date | None] = mapped_column()
    end_date: Mapped[date | None] = mapped_column()
    budget_inr: Mapped[int | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(32), default="draft", server_default="draft")
    itinerary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column()  # soft delete (§5.6 #10)

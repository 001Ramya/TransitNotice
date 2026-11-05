from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Agency(Base):
    __tablename__ = "agencies"
    __table_args__ = (UniqueConstraint("key", name="uq_agencies_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    notices: Mapped[list["Notice"]] = relationship(back_populates="agency")


class Notice(Base):
    __tablename__ = "notices"
    __table_args__ = (
        UniqueConstraint("agency_id", "external_id", name="uq_notice_agency_external"),
        Index("ix_notices_last_confirmed_at", "last_confirmed_at"),
        Index("ix_notices_advisory_type", "advisory_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agency_id: Mapped[int] = mapped_column(ForeignKey("agencies.id", ondelete="RESTRICT"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(180), nullable=False)
    route_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    area: Mapped[str] = mapped_column(String(240), default="Network-wide", nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    advisory_type: Mapped[str] = mapped_column(String(60), nullable=False)
    summary: Mapped[str] = mapped_column(String(600), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    change_summary: Mapped[str] = mapped_column(String(800), default="First observed", nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    missing_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_withdrawn: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    agency: Mapped[Agency] = relationship(back_populates="notices")
    revisions: Mapped[list["NoticeRevision"]] = relationship(back_populates="notice", cascade="all, delete-orphan")
    deliveries: Mapped[list["AlertDelivery"]] = relationship(back_populates="notice", cascade="all, delete-orphan")


class NoticeRevision(Base):
    __tablename__ = "notice_revisions"
    __table_args__ = (UniqueConstraint("notice_id", "revision_number", name="uq_revision_notice_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notice_id: Mapped[str] = mapped_column(ForeignKey("notices.id", ondelete="CASCADE"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    change_summary: Mapped[str] = mapped_column(String(800), nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    notice: Mapped[Notice] = relationship(back_populates="revisions")


class CollectorRun(Base):
    __tablename__ = "collector_runs"
    __table_args__ = (Index("ix_collector_runs_source_started", "source_key", "started_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_key: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    notice_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class AlertDelivery(Base):
    __tablename__ = "alert_deliveries"
    __table_args__ = (
        UniqueConstraint(
            "notice_id", "revision_number", "channel", "recipient",
            name="uq_alert_notice_revision_channel_recipient",
        ),
        Index("ix_alert_deliveries_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notice_id: Mapped[str] = mapped_column(ForeignKey("notices.id", ondelete="CASCADE"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    recipient: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    subscriber_filter: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    notice: Mapped[Notice] = relationship(back_populates="deliveries")

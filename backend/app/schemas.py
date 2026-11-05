from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NoticeOut(BaseModel):
    id: str
    agency: str
    route_ids: list[str]
    area: str
    source_url: str | None
    advisory_type: str
    summary: str
    content_text: str
    published_at: datetime | None
    valid_from: datetime | None
    valid_to: datetime | None
    status: str
    last_observed_at: datetime
    last_confirmed_at: datetime
    revision_number: int
    change_summary: str
    is_demo: bool
    is_stale: bool


class RevisionOut(BaseModel):
    id: int
    revision_number: int
    change_summary: str
    snapshot: dict
    observed_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DeliveryOut(BaseModel):
    id: int
    notice_id: str
    revision_number: int
    channel: str
    recipient: str
    status: str
    subject: str
    created_at: datetime
    delivered_at: datetime | None
    error_message: str | None
    model_config = ConfigDict(from_attributes=True)


class SourceOut(BaseModel):
    key: str
    agency: str
    source_url: str
    enabled: bool
    state: str
    last_checked_at: datetime | None
    last_success_at: datetime | None
    last_notice_count: int
    message: str
    is_demo: bool


class SettingsOut(BaseModel):
    demo_mode: bool
    scheduler_enabled: bool
    refresh_interval_minutes: int
    stale_after_minutes: int
    alert_mode: str
    smtp_configured: bool
    mbta_enabled: bool
    mbta_key_configured: bool
    cta_terms_accepted: bool


class RefreshOut(BaseModel):
    message: str
    started_at: datetime
    results: list[dict]

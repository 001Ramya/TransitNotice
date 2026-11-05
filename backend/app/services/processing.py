from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Agency, Notice, NoticeRevision, utc_now


@dataclass(frozen=True)
class NormalizedNotice:
    external_id: str
    route_ids: list[str]
    area: str
    source_url: str | None
    advisory_type: str
    summary: str
    content_text: str
    published_at: datetime | None
    valid_from: datetime | None
    valid_to: datetime | None


def _date_text(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value else None


def notice_snapshot(notice: Notice | NormalizedNotice) -> dict[str, Any]:
    if isinstance(notice, Notice):
        values = {
            "external_id": notice.external_id,
            "route_ids": notice.route_ids,
            "area": notice.area,
            "source_url": notice.source_url,
            "advisory_type": notice.advisory_type,
            "summary": notice.summary,
            "content_text": notice.content_text,
            "published_at": _date_text(notice.published_at),
            "valid_from": _date_text(notice.valid_from),
            "valid_to": _date_text(notice.valid_to),
            "is_withdrawn": notice.is_withdrawn,
        }
    else:
        values = asdict(notice)
        values["route_ids"] = sorted(set(values["route_ids"]))
        for key in ("published_at", "valid_from", "valid_to"):
            values[key] = _date_text(values[key])
        values["is_withdrawn"] = False
    return values


def content_hash(snapshot: dict[str, Any]) -> str:
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def current_status(notice: Notice, now: datetime | None = None) -> str:
    now = now or utc_now()
    if notice.is_withdrawn:
        return "withdrawn"
    if notice.valid_from and notice.valid_from > now:
        return "upcoming"
    if notice.valid_to and notice.valid_to < now:
        return "expired"
    return "active"


def _change_summary(old: Notice, new: NormalizedNotice) -> str:
    changes: list[str] = []
    if sorted(old.route_ids or []) != sorted(set(new.route_ids)):
        changes.append("affected routes changed")
    if old.area != new.area:
        changes.append("affected area changed")
    if old.advisory_type != new.advisory_type:
        changes.append("advisory type changed")
    if old.summary != new.summary or old.content_text != new.content_text:
        changes.append("notice text updated")
    if old.valid_from != new.valid_from:
        changes.append("start time changed")
    if old.valid_to != new.valid_to:
        if old.valid_to and new.valid_to and new.valid_to > old.valid_to:
            changes.append("service window extended")
        elif old.valid_to and new.valid_to and new.valid_to < old.valid_to:
            changes.append("service window shortened")
        else:
            changes.append("end time changed")
    if old.source_url != new.source_url:
        changes.append("source link changed")
    return ", ".join(changes) or "notice details updated"


def _notify(session: Session, notice: Notice, reason: str) -> None:
    from app.services.alerts import log_alert

    log_alert(session, notice, reason)


def process_snapshot(
    session: Session,
    agency: Agency,
    records: list[NormalizedNotice],
    *,
    complete_snapshot: bool,
    observed_at: datetime | None = None,
    is_demo: bool = False,
) -> dict[str, int]:
    """Idempotently upsert one source snapshot and append only real revisions."""
    observed_at = observed_at or utc_now()
    deduplicated: dict[str, NormalizedNotice] = {}
    for record in records:
        if not record.external_id.strip():
            continue
        deduplicated.setdefault(record.external_id, record)

    counts = {"notices": len(deduplicated), "new": 0, "updated": 0, "withdrawn": 0}
    seen_ids: set[str] = set()
    existing_rows = session.scalars(select(Notice).where(Notice.agency_id == agency.id)).all()
    existing_by_external = {row.external_id: row for row in existing_rows}

    for external_id, record in deduplicated.items():
        seen_ids.add(external_id)
        snapshot = notice_snapshot(record)
        fingerprint = content_hash(snapshot)
        notice = existing_by_external.get(external_id)
        if notice is None:
            notice = Notice(
                agency_id=agency.id,
                external_id=external_id,
                route_ids=sorted(set(record.route_ids)),
                area=record.area or "Network-wide",
                source_url=record.source_url,
                advisory_type=record.advisory_type,
                summary=record.summary,
                content_text=record.content_text,
                published_at=record.published_at,
                valid_from=record.valid_from,
                valid_to=record.valid_to,
                content_hash=fingerprint,
                revision_number=1,
                change_summary="First observed from the official source",
                first_seen_at=observed_at,
                last_observed_at=observed_at,
                last_confirmed_at=observed_at,
                is_demo=is_demo,
            )
            session.add(notice)
            session.flush()
            session.add(
                NoticeRevision(
                    notice_id=notice.id,
                    revision_number=1,
                    change_summary=notice.change_summary,
                    snapshot=snapshot,
                    content_hash=fingerprint,
                    observed_at=observed_at,
                )
            )
            _notify(session, notice, "New advisory observed")
            counts["new"] += 1
            existing_by_external[external_id] = notice
            continue

        notice.last_observed_at = observed_at
        notice.last_confirmed_at = observed_at
        notice.missing_streak = 0
        if notice.is_withdrawn:
            notice.is_withdrawn = False
        if notice.content_hash != fingerprint:
            change = _change_summary(notice, record)
            notice.route_ids = sorted(set(record.route_ids))
            notice.area = record.area or "Network-wide"
            notice.source_url = record.source_url
            notice.advisory_type = record.advisory_type
            notice.summary = record.summary
            notice.content_text = record.content_text
            notice.published_at = record.published_at
            notice.valid_from = record.valid_from
            notice.valid_to = record.valid_to
            notice.content_hash = fingerprint
            notice.revision_number += 1
            notice.change_summary = change
            notice.is_demo = is_demo
            session.flush()
            session.add(
                NoticeRevision(
                    notice_id=notice.id,
                    revision_number=notice.revision_number,
                    change_summary=change,
                    snapshot=snapshot,
                    content_hash=fingerprint,
                    observed_at=observed_at,
                )
            )
            _notify(session, notice, "Advisory revised: " + change)
            counts["updated"] += 1

    if complete_snapshot:
        for notice in existing_rows:
            if notice.external_id in seen_ids or notice.is_withdrawn:
                continue
            notice.last_observed_at = observed_at
            if current_status(notice, observed_at) == "expired":
                continue
            notice.missing_streak += 1
            if notice.missing_streak < 2:
                continue
            notice.is_withdrawn = True
            notice.last_confirmed_at = observed_at
            notice.revision_number += 1
            notice.change_summary = "Source no longer lists this advisory after two complete checks"
            withdrawn_snapshot = notice_snapshot(notice)
            withdrawn_fingerprint = content_hash(withdrawn_snapshot)
            notice.content_hash = withdrawn_fingerprint
            session.flush()
            session.add(
                NoticeRevision(
                    notice_id=notice.id,
                    revision_number=notice.revision_number,
                    change_summary=notice.change_summary,
                    snapshot=withdrawn_snapshot,
                    content_hash=withdrawn_fingerprint,
                    observed_at=observed_at,
                )
            )
            _notify(session, notice, "Advisory withdrawn by source")
            counts["withdrawn"] += 1

    session.flush()
    return counts

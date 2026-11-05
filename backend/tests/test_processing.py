from datetime import timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base
from app.models import Agency, Notice, NoticeRevision, utc_now
from app.services.processing import NormalizedNotice, process_snapshot


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    database_session = factory()
    previous_mode = settings.alert_mode
    settings.alert_mode = "demo"
    try:
        yield database_session
    finally:
        settings.alert_mode = previous_mode
        database_session.close()


@pytest.fixture()
def agency(session):
    item = Agency(
        key="test-agency",
        name="Test Transit",
        source_url="https://example.test/official-alerts",
        is_demo=True,
    )
    session.add(item)
    session.commit()
    return item


def record(*, summary="Route 14 detour", valid_to=None):
    timestamp = utc_now()
    return NormalizedNotice(
        external_id="ALERT-14",
        route_ids=["14"],
        area="Market District",
        source_url="https://example.test/official-alerts/ALERT-14",
        advisory_type="ROUTE_DIVERSION",
        summary=summary,
        content_text="A temporary route diversion is in effect.",
        published_at=timestamp,
        valid_from=timestamp,
        valid_to=valid_to or timestamp + timedelta(hours=2),
    )


def test_repeat_snapshot_is_idempotent(session, agency):
    first = record()
    first_counts = process_snapshot(session, agency, [first], complete_snapshot=True)
    session.commit()
    second_counts = process_snapshot(session, agency, [first], complete_snapshot=True)
    session.commit()

    notice = session.scalar(select(Notice))
    revisions = session.scalars(select(NoticeRevision)).all()
    assert first_counts["new"] == 1
    assert second_counts["new"] == 0
    assert second_counts["updated"] == 0
    assert notice.revision_number == 1
    assert len(revisions) == 1


def test_extension_creates_history_revision(session, agency):
    old = record(valid_to=utc_now() + timedelta(hours=2))
    process_snapshot(session, agency, [old], complete_snapshot=True)
    session.commit()
    extended = record(valid_to=utc_now() + timedelta(hours=8))
    result = process_snapshot(session, agency, [extended], complete_snapshot=True)
    session.commit()

    notice = session.scalar(select(Notice))
    history = session.scalars(
        select(NoticeRevision).order_by(NoticeRevision.revision_number)
    ).all()
    assert result["updated"] == 1
    assert notice.revision_number == 2
    assert "extended" in notice.change_summary
    assert len(history) == 2


def test_notice_is_withdrawn_only_after_two_complete_absences(session, agency):
    process_snapshot(session, agency, [record()], complete_snapshot=True)
    session.commit()
    first_missing = process_snapshot(session, agency, [], complete_snapshot=True)
    session.commit()
    notice = session.scalar(select(Notice))
    assert first_missing["withdrawn"] == 0
    assert notice.is_withdrawn is False

    second_missing = process_snapshot(session, agency, [], complete_snapshot=True)
    session.commit()
    notice = session.scalar(select(Notice))
    assert second_missing["withdrawn"] == 1
    assert notice.is_withdrawn is True
    assert notice.revision_number == 2

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Agency, AlertDelivery, CollectorRun, Notice, NoticeRevision, utc_now
from app.services.processing import NormalizedNotice, content_hash, notice_snapshot, process_snapshot

DEMO_AGENCY_KEY = "demo"


def seed_demo_data(session: Session) -> None:
    existing = session.scalar(select(Agency.id).where(Agency.key == DEMO_AGENCY_KEY))
    if existing:
        return

    now = utc_now()
    agency = Agency(
        key=DEMO_AGENCY_KEY,
        name="HarborLink Demo Network",
        source_url="",
        is_demo=True,
    )
    session.add(agency)
    session.flush()
    examples = [
        NormalizedNotice(
            external_id="DEMO-101",
            route_ids=["14"],
            area="Riverside Market",
            source_url=None,
            advisory_type="ROUTE_DIVERSION",
            summary="Route 14 is using a temporary Market Street detour",
            content_text="Demonstration only: Route 14 buses use Oak Avenue between 8th Street and Harbor Road while a fictional utility crew works near Riverside Market.",
            published_at=now - timedelta(hours=2),
            valid_from=now - timedelta(hours=1),
            valid_to=now + timedelta(hours=5),
        ),
        NormalizedNotice(
            external_id="DEMO-102",
            route_ids=["R2", "R5"],
            area="Central Station",
            source_url=None,
            advisory_type="PLANNED_WORK",
            summary="Weekend platform work planned at Central Station",
            content_text="Demonstration only: Step-free access at the east entrance is scheduled to close overnight. Use the north entrance during the stated service window.",
            published_at=now - timedelta(days=1),
            valid_from=now + timedelta(days=2),
            valid_to=now + timedelta(days=4),
        ),
        NormalizedNotice(
            external_id="DEMO-103",
            route_ids=["31"],
            area="Museum Quarter",
            source_url=None,
            advisory_type="SERVICE_INTERRUPTION",
            summary="Route 31 service interruption ended",
            content_text="Demonstration only: The fictional Route 31 interruption has ended. This record is retained to show an expired notice in the history.",
            published_at=now - timedelta(days=4),
            valid_from=now - timedelta(days=4),
            valid_to=now - timedelta(days=2),
        ),
        NormalizedNotice(
            external_id="DEMO-104",
            route_ids=["R2"],
            area="North Pier",
            source_url=None,
            advisory_type="DELAY",
            summary="Minor delays on Route R2 near North Pier",
            content_text="Demonstration only: Expect additional travel time through the North Pier corridor. Allow a few extra minutes for connections.",
            published_at=now - timedelta(minutes=20),
            valid_from=now - timedelta(minutes=15),
            valid_to=None,
        ),
        NormalizedNotice(
            external_id="DEMO-105",
            route_ids=["7", "14"],
            area="Harbor Bridge",
            source_url=None,
            advisory_type="SERVICE_ADVISORY",
            summary="Bridge traffic may affect buses this afternoon",
            content_text="Demonstration only: Congestion around the fictional Harbor Bridge may affect Routes 7 and 14. No end time has been provided in this example.",
            published_at=now - timedelta(minutes=45),
            valid_from=now - timedelta(minutes=30),
            valid_to=None,
        ),
        NormalizedNotice(
            external_id="DEMO-106",
            route_ids=["R5"],
            area="Garden District",
            source_url=None,
            advisory_type="ACCESSIBILITY",
            summary="Elevator access unavailable at Garden District",
            content_text="Demonstration only: Use the street-level entrance while the fictional station elevator is out of service.",
            published_at=now - timedelta(hours=3),
            valid_from=now - timedelta(hours=2),
            valid_to=now + timedelta(days=1),
        ),
    ]
    process_snapshot(session, agency, examples, complete_snapshot=False, observed_at=now, is_demo=True)

    revised = examples[0]
    extended = NormalizedNotice(
        external_id=revised.external_id,
        route_ids=revised.route_ids,
        area=revised.area,
        source_url=revised.source_url,
        advisory_type=revised.advisory_type,
        summary=revised.summary,
        content_text=revised.content_text + " In this demo revision, the detour end time has been extended by one hour.",
        published_at=revised.published_at,
        valid_from=revised.valid_from,
        valid_to=(revised.valid_to or now) + timedelta(hours=1),
    )
    process_snapshot(session, agency, [extended], complete_snapshot=False, observed_at=now, is_demo=True)

    withdrawn = examples[-1]
    withdrawn_notice = session.scalar(
        select(Notice).where(Notice.agency_id == agency.id, Notice.external_id == withdrawn.external_id)
    )
    if withdrawn_notice:
        withdrawn_notice.is_withdrawn = True
        withdrawn_notice.revision_number += 1
        withdrawn_notice.change_summary = "Demonstration: source withdrew this notice"
        withdrawn_snapshot = notice_snapshot(withdrawn_notice)
        withdrawn_hash = content_hash(withdrawn_snapshot)
        withdrawn_notice.content_hash = withdrawn_hash
        session.add(
            NoticeRevision(
                notice_id=withdrawn_notice.id,
                revision_number=withdrawn_notice.revision_number,
                change_summary=withdrawn_notice.change_summary,
                snapshot=withdrawn_snapshot,
                content_hash=withdrawn_hash,
                observed_at=now,
            )
        )
        session.add(
            AlertDelivery(
                notice_id=withdrawn_notice.id,
                revision_number=withdrawn_notice.revision_number,
                channel="demo",
                recipient="local-demo",
                status="logged",
                subject="TransitNotice: " + withdrawn_notice.summary,
                created_at=now,
                subscriber_filter={},
            )
        )

    session.add(
        CollectorRun(
            source_key="demo",
            started_at=now,
            finished_at=now,
            state="demo",
            notice_count=len(examples),
            new_count=len(examples),
            updated_count=1,
        )
    )
    session.commit()

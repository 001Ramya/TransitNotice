"""Initial TransitNotice schema.

Revision ID: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agencies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("key", name="uq_agencies_key"),
    )
    op.create_table(
        "notices",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("agency_id", sa.Integer(), sa.ForeignKey("agencies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("external_id", sa.String(length=180), nullable=False),
        sa.Column("route_ids", sa.JSON(), nullable=False),
        sa.Column("area", sa.String(length=240), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("advisory_type", sa.String(length=60), nullable=False),
        sa.Column("summary", sa.String(length=600), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("change_summary", sa.String(length=800), nullable=False, server_default="First observed"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("missing_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_withdrawn", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("agency_id", "external_id", name="uq_notice_agency_external"),
    )
    op.create_index("ix_notices_agency_id", "notices", ["agency_id"])
    op.create_index("ix_notices_last_confirmed_at", "notices", ["last_confirmed_at"])
    op.create_index("ix_notices_advisory_type", "notices", ["advisory_type"])
    op.create_table(
        "notice_revisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("notice_id", sa.String(length=36), sa.ForeignKey("notices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("change_summary", sa.String(length=800), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("notice_id", "revision_number", name="uq_revision_notice_version"),
    )
    op.create_index("ix_notice_revisions_observed_at", "notice_revisions", ["observed_at"])
    op.create_table(
        "collector_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_key", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("notice_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
    )
    op.create_index("ix_collector_runs_source_started", "collector_runs", ["source_key", "started_at"])
    op.create_table(
        "alert_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("notice_id", sa.String(length=36), sa.ForeignKey("notices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("recipient", sa.String(length=320), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("subject", sa.String(length=300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("subscriber_filter", sa.JSON(), nullable=False, server_default="{}"),
        sa.UniqueConstraint(
            "notice_id", "revision_number", "channel", "recipient",
            name="uq_alert_notice_revision_channel_recipient",
        ),
    )
    op.create_index("ix_alert_deliveries_created_at", "alert_deliveries", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_alert_deliveries_created_at", table_name="alert_deliveries")
    op.drop_table("alert_deliveries")
    op.drop_index("ix_collector_runs_source_started", table_name="collector_runs")
    op.drop_table("collector_runs")
    op.drop_index("ix_notice_revisions_observed_at", table_name="notice_revisions")
    op.drop_table("notice_revisions")
    op.drop_index("ix_notices_advisory_type", table_name="notices")
    op.drop_index("ix_notices_last_confirmed_at", table_name="notices")
    op.drop_index("ix_notices_agency_id", table_name="notices")
    op.drop_table("notices")
    op.drop_table("agencies")

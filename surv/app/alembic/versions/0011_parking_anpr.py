"""Add parking management and ANPR tables

Revision ID: 0011_parking_anpr
Revises: 0010_recording_mode
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_parking_anpr"
down_revision = "0010_recording_mode"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Optional pg_trgm extension for fuzzy plate search ───────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # ── 2. Parking Zone ────────────────────────────────────────────────────────
    op.create_table(
        "parking_zone",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("customer_site_id", sa.BigInteger(), sa.ForeignKey("customer_site.id"), nullable=True),
        sa.Column("zone_code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("vehicle_type", sa.String(50), nullable=False, server_default="ALL"),
        sa.Column("total_capacity", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("current_occupancy", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("customer_site_id", "zone_code", name="uq_parking_zone_site_code"),
    )
    op.create_index("ix_parking_zone_id", "parking_zone", ["id"])
    op.create_index("ix_parking_zone_code", "parking_zone", ["zone_code"])
    op.create_index("ix_parking_zone_site", "parking_zone", ["customer_site_id"])

    # ── 3. Parking Lane ────────────────────────────────────────────────────────
    op.create_table(
        "parking_lane",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("parking_zone_id", sa.BigInteger(), sa.ForeignKey("parking_zone.id", ondelete="CASCADE"), nullable=True),
        sa.Column("customer_site_id", sa.BigInteger(), sa.ForeignKey("customer_site.id"), nullable=True),
        sa.Column("lane_code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("lane_type", sa.String(20), nullable=False),
        sa.Column("camera_id", sa.Integer(), sa.ForeignKey("survapp_camera_master.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("customer_site_id", "lane_code", name="uq_parking_lane_site_code"),
    )
    op.create_index("ix_parking_lane_id", "parking_lane", ["id"])
    op.create_index("ix_parking_lane_zone", "parking_lane", ["parking_zone_id"])
    op.create_index("ix_parking_lane_site", "parking_lane", ["customer_site_id"])

    # ── 4. Parking Session ─────────────────────────────────────────────────────
    op.create_table(
        "parking_session",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("customer_site_id", sa.BigInteger(), sa.ForeignKey("customer_site.id"), nullable=True),
        sa.Column("parking_zone_id", sa.BigInteger(), sa.ForeignKey("parking_zone.id"), nullable=False),
        sa.Column("entry_lane_id", sa.BigInteger(), sa.ForeignKey("parking_lane.id"), nullable=True),
        sa.Column("exit_lane_id", sa.BigInteger(), sa.ForeignKey("parking_lane.id"), nullable=True),
        sa.Column("vehicle_number", sa.String(50), nullable=False),
        sa.Column("normalized_plate", sa.String(50), nullable=False),
        sa.Column("vehicle_type", sa.String(50), nullable=False, server_default="LMV"),
        sa.Column("entry_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("exit_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("entry_slip_number", sa.String(100), nullable=False, unique=True),
        sa.Column("fee_amount", sa.Numeric(10, 2), nullable=True, server_default="0.0"),
        sa.Column("anpr_transaction_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_parking_session_id", "parking_session", ["id"])
    op.create_index("ix_parking_session_vehicle", "parking_session", ["vehicle_number"])
    op.create_index("ix_parking_session_norm_plate", "parking_session", ["normalized_plate"])
    op.create_index("ix_parking_session_status", "parking_session", ["status"])
    op.create_index("ix_parking_session_slip", "parking_session", ["entry_slip_number"])
    op.create_index("ix_parking_session_site_status", "parking_session", ["customer_site_id", "status"])
    op.create_index("ix_parking_session_plate_status", "parking_session", ["normalized_plate", "status"])

    # ── 5. ANPR Transaction ────────────────────────────────────────────────────
    op.create_table(
        "anpr_transaction",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("customer_site_id", sa.BigInteger(), sa.ForeignKey("customer_site.id"), nullable=True),
        sa.Column("camera_id", sa.Integer(), sa.ForeignKey("survapp_camera_master.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lane_id", sa.BigInteger(), nullable=True),
        sa.Column("plate_number", sa.String(50), nullable=False),
        sa.Column("normalized_plate", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("vehicle_type", sa.String(50), nullable=True, server_default="CAR"),
        sa.Column("vehicle_color", sa.String(50), nullable=True),
        sa.Column("speed_kmh", sa.Float(), nullable=True),
        sa.Column("direction", sa.String(20), nullable=True),
        sa.Column("snapshot_key", sa.String(500), nullable=True),
        sa.Column("video_reference", sa.String(500), nullable=True),
        sa.Column("processing_source", sa.String(50), nullable=False, server_default="edge_lpu"),
        sa.Column("is_corrected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("original_plate", sa.String(50), nullable=True),
        sa.Column("corrected_by_user_id", sa.BigInteger(), sa.ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("correction_notes", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_anpr_transaction_id", "anpr_transaction", ["id"])
    op.create_index("ix_anpr_plate", "anpr_transaction", ["plate_number"])
    op.create_index("ix_anpr_norm_plate", "anpr_transaction", ["normalized_plate"])
    op.create_index("ix_anpr_captured_at", "anpr_transaction", ["captured_at"])
    op.create_index("ix_anpr_site_captured", "anpr_transaction", ["customer_site_id", "captured_at"])
    op.create_index("ix_anpr_camera_captured", "anpr_transaction", ["camera_id", "captured_at"])

    # GIN trgm index for fast fuzzy license plate search
    try:
        op.execute("CREATE INDEX IF NOT EXISTS ix_anpr_trgm_plate ON anpr_transaction USING gin (normalized_plate gin_trgm_ops);")
    except Exception:
        pass

    # ── 6. Vehicle Watchlist ───────────────────────────────────────────────────
    op.create_table(
        "vehicle_watchlist",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("plate_number", sa.String(50), nullable=False),
        sa.Column("normalized_plate", sa.String(50), nullable=False, unique=True),
        sa.Column("category", sa.String(50), nullable=False, server_default="WANTED"),
        sa.Column("severity", sa.String(20), nullable=False, server_default="HIGH"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("case_number", sa.String(100), nullable=True),
        sa.Column("reporting_authority", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by_user_id", sa.BigInteger(), sa.ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_vehicle_watchlist_id", "vehicle_watchlist", ["id"])
    op.create_index("ix_vehicle_watchlist_plate", "vehicle_watchlist", ["plate_number"])
    op.create_index("ix_vehicle_watchlist_norm_plate", "vehicle_watchlist", ["normalized_plate"])

    # ── 7. Watchlist Alert ─────────────────────────────────────────────────────
    op.create_table(
        "watchlist_alert",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("watchlist_id", sa.BigInteger(), sa.ForeignKey("vehicle_watchlist.id", ondelete="CASCADE"), nullable=False),
        sa.Column("anpr_transaction_id", sa.BigInteger(), sa.ForeignKey("anpr_transaction.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plate_number", sa.String(50), nullable=False),
        sa.Column("camera_id", sa.Integer(), sa.ForeignKey("survapp_camera_master.id", ondelete="SET NULL"), nullable=True),
        sa.Column("customer_site_id", sa.BigInteger(), sa.ForeignKey("customer_site.id", ondelete="SET NULL"), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="HIGH"),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("acknowledged_by_user_id", sa.BigInteger(), sa.ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_watchlist_alert_id", "watchlist_alert", ["id"])
    op.create_index("ix_watchlist_alert_status", "watchlist_alert", ["status"])
    op.create_index("ix_watchlist_alert_status_created", "watchlist_alert", ["status", "created_at"])


def downgrade() -> None:
    op.drop_table("watchlist_alert")
    op.drop_table("vehicle_watchlist")
    op.drop_table("anpr_transaction")
    op.drop_table("parking_session")
    op.drop_table("parking_lane")
    op.drop_table("parking_zone")

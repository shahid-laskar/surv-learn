"""Add incident management and evidence package tables

Revision ID: 0012_incident_evidence
Revises: 0011_parking_anpr
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_incident_evidence"
down_revision = "0011_parking_anpr"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Incident Table ──────────────────────────────────────────────────────
    op.create_table(
        "incident",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("incident_number", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="NEW"),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("source_id", sa.BigInteger(), nullable=True),
        sa.Column("camera_id", sa.Integer(), sa.ForeignKey("survapp_camera_master.id", ondelete="SET NULL"), nullable=True),
        sa.Column("customer_site_id", sa.BigInteger(), sa.ForeignKey("customer_site.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_to_user_id", sa.BigInteger(), sa.ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), sa.ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evidence_package_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_incident_id", "incident", ["id"])
    op.create_index("ix_incident_number", "incident", ["incident_number"])
    op.create_index("ix_incident_status", "incident", ["status"])
    op.create_index("ix_incident_severity", "incident", ["severity"])
    op.create_index("ix_incident_camera", "incident", ["camera_id"])
    op.create_index("ix_incident_site", "incident", ["customer_site_id"])
    op.create_index("ix_incident_assigned", "incident", ["assigned_to_user_id"])
    op.create_index("ix_incident_created_at", "incident", ["created_at"])

    # ── 2. Incident Timeline Table ─────────────────────────────────────────────
    op.create_table(
        "incident_timeline",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("incident_id", sa.BigInteger(), sa.ForeignKey("incident.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", sa.String(50), nullable=True),
        sa.Column("to_status", sa.String(50), nullable=False),
        sa.Column("changed_by_user_id", sa.BigInteger(), sa.ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_incident_timeline_id", "incident_timeline", ["id"])
    op.create_index("ix_incident_timeline_incident", "incident_timeline", ["incident_id"])
    op.create_index("ix_incident_timeline_created_at", "incident_timeline", ["created_at"])

    # ── 3. Evidence Package Table ──────────────────────────────────────────────
    op.create_table(
        "evidence_package",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("package_number", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("incident_id", sa.BigInteger(), sa.ForeignKey("incident.id", ondelete="SET NULL"), nullable=True),
        sa.Column("camera_id", sa.Integer(), sa.ForeignKey("survapp_camera_master.id", ondelete="SET NULL"), nullable=True),
        sa.Column("customer_site_id", sa.BigInteger(), sa.ForeignKey("customer_site.id", ondelete="SET NULL"), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("exported_by_user_id", sa.BigInteger(), sa.ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_sealed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_evidence_package_id", "evidence_package", ["id"])
    op.create_index("ix_evidence_package_number", "evidence_package", ["package_number"])
    op.create_index("ix_evidence_package_incident", "evidence_package", ["incident_id"])
    op.create_index("ix_evidence_package_camera", "evidence_package", ["camera_id"])


def downgrade() -> None:
    op.drop_table("evidence_package")
    op.drop_table("incident_timeline")
    op.drop_table("incident")

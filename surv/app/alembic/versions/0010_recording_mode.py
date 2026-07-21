"""Add recording_mode, guard secs to camera; recording_type, has_motion to video_segment

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_recording_mode"
down_revision = "0009_stream_protocol"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Camera master — recording mode ────────────────────────────────────────
    op.add_column(
        "survapp_camera_master",
        sa.Column(
            "recording_mode",
            sa.String(20),
            nullable=False,
            server_default="full",
        ),
    )
    op.add_column(
        "survapp_camera_master",
        sa.Column(
            "motion_pre_guard_secs",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
    )
    op.add_column(
        "survapp_camera_master",
        sa.Column(
            "motion_post_guard_secs",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
    )

    # ── Video segment — type tagging ───────────────────────────────────────────
    op.add_column(
        "survapp_video_segment",
        sa.Column(
            "recording_type",
            sa.String(20),
            nullable=False,
            server_default="full",
        ),
    )
    op.add_column(
        "survapp_video_segment",
        sa.Column(
            "has_motion",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )

    # Index to speed up motion-only cleaner queries
    op.create_index(
        "ix_video_segment_camera_type",
        "survapp_video_segment",
        ["camera_id", "recording_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_video_segment_camera_type", table_name="survapp_video_segment")
    op.drop_column("survapp_video_segment", "has_motion")
    op.drop_column("survapp_video_segment", "recording_type")
    op.drop_column("survapp_camera_master", "motion_post_guard_secs")
    op.drop_column("survapp_camera_master", "motion_pre_guard_secs")
    op.drop_column("survapp_camera_master", "recording_mode")

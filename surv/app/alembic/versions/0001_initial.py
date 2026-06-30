"""Initial schema — camera, motion_event, video_segment

Revision ID: 0001
Revises:
Create Date: 2026-06-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "survapp_camera_master",
        sa.Column("id",             sa.Integer(),     primary_key=True),
        sa.Column("cam_id",         sa.String(100),   nullable=False),
        sa.Column("cam_name",       sa.String(200)),
        sa.Column("cam_ip",         sa.String(50),    nullable=False),
        sa.Column("cam_port",       sa.Integer(),     server_default="554"),
        sa.Column("onvif_port",     sa.Integer(),     server_default="80"),
        sa.Column("rtsp_url",       sa.String(500)),
        sa.Column("onvif_username", sa.String(100),   server_default="admin"),
        sa.Column("onvif_password", sa.String(100),   server_default="admin"),
        sa.Column("is_active",      sa.Boolean(),     nullable=False, server_default="true"),
        sa.Column("is_online",      sa.Boolean(),     nullable=False, server_default="false"),
        sa.Column("motion_active",  sa.Boolean(),     nullable=False, server_default="true"),
        sa.Column("last_seen",      sa.DateTime(timezone=True)),
        sa.Column("created_at",     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_camera_cam_id",   "survapp_camera_master", ["cam_id"],  unique=True)
    op.create_index("ix_camera_id",       "survapp_camera_master", ["id"])

    op.create_table(
        "survapp_motion_event",
        sa.Column("id",           sa.Integer(),              primary_key=True),
        sa.Column("camera_id",    sa.Integer(),              nullable=False),
        sa.Column("motion_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("motion_end",   sa.DateTime(timezone=True)),
        sa.Column("is_active",    sa.Boolean(),              nullable=False, server_default="true"),
        sa.Column("created_at",   sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["camera_id"], ["survapp_camera_master.id"]),
    )
    op.create_index("ix_motion_event_id",            "survapp_motion_event", ["id"])
    op.create_index("ix_motion_event_camera_id",     "survapp_motion_event", ["camera_id"])
    op.create_index("ix_motion_event_camera_active", "survapp_motion_event",
                    ["camera_id", "is_active"])

    op.create_table(
        "survapp_video_segment",
        sa.Column("id",               sa.Integer(),              primary_key=True),
        sa.Column("camera_id",        sa.Integer(),              nullable=False),
        sa.Column("object_key",       sa.String(500),            nullable=False),
        sa.Column("bucket",           sa.String(100),            nullable=False,
                  server_default="recordings"),
        sa.Column("segment_start",    sa.DateTime(timezone=True), nullable=False),
        sa.Column("segment_end",      sa.DateTime(timezone=True)),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("file_size_bytes",  sa.BigInteger()),
        sa.Column("deleted_at",       sa.DateTime(timezone=True)),
        sa.Column("created_at",       sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["camera_id"], ["survapp_camera_master.id"]),
        sa.UniqueConstraint("object_key", name="uq_video_segment_object_key"),
    )
    op.create_index("ix_video_segment_id",           "survapp_video_segment", ["id"])
    op.create_index("ix_video_segment_camera_id",    "survapp_video_segment", ["camera_id"])
    op.create_index("ix_video_segment_camera_start", "survapp_video_segment",
                    ["camera_id", "segment_start"])


def downgrade() -> None:
    op.drop_table("survapp_video_segment")
    op.drop_table("survapp_motion_event")
    op.drop_table("survapp_camera_master")
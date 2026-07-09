"""Edge segment index and site enrollment secret

Revision ID: 0008_edge_segments
Revises: 0007_mobile_devices
Create Date: 2026-07-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_edge_segments"
down_revision: Union[str, None] = "0007_mobile_devices"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "nvr_node",
        sa.Column("site_enrollment_secret", sa.String(length=64), nullable=True),
    )

    op.create_table(
        "edge_video_segment",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("camera_id", sa.Integer(), sa.ForeignKey("survapp_camera_master.id"), nullable=True),
        sa.Column("nvr_node_id", sa.Integer(), sa.ForeignKey("nvr_node.id"), nullable=True),
        sa.Column("segment_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("segment_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("local_path", sa.String(length=500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nvr_node_id", "camera_id", "segment_start", name="uq_edge_segment"),
    )
    op.create_index(
        "ix_edge_video_segment_camera_start",
        "edge_video_segment",
        ["camera_id", "segment_start"],
    )


def downgrade() -> None:
    op.drop_index("ix_edge_video_segment_camera_start", table_name="edge_video_segment")
    op.drop_table("edge_video_segment")
    op.drop_column("nvr_node", "site_enrollment_secret")

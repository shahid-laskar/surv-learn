"""Add stream_protocol to camera master

Revision ID: 0009_stream_protocol
Revises: 0008_edge_segments
Create Date: 2026-07-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_stream_protocol"
down_revision: Union[str, None] = "0008_edge_segments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "survapp_camera_master",
        sa.Column(
            "stream_protocol",
            sa.String(length=16),
            nullable=False,
            server_default="rtsp",
        ),
    )


def downgrade() -> None:
    op.drop_column("survapp_camera_master", "stream_protocol")

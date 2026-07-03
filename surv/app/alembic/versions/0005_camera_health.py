"""Camera Health Monitoring

Revision ID: 0005_camera_health
Revises: 0004_bsnl_masters
Create Date: 2026-07-03 12:00:00.000000

Adds:
  - camera_status_log: immutable history of every online/offline transition
    with computed duration_seconds filled on the *next* transition
  - survapp_camera_master.retention_days: per-camera recording retention
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0005_camera_health'
down_revision: Union[str, None] = '0004_bsnl_masters'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. camera_status_log — immutable audit trail of online/offline transitions
    op.create_table(
        'camera_status_log',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column(
            'camera_id', sa.Integer(),
            sa.ForeignKey('survapp_camera_master.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('status', sa.String(20), nullable=False),          # 'online' | 'offline'
        sa.Column(
            'changed_at', sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'), nullable=False,
        ),
        # Filled on the *next* transition: how long did this status last?
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
    )
    op.create_index(
        'ix_camera_status_log_camera_changed',
        'camera_status_log', ['camera_id', 'changed_at'],
    )

    # 2. Per-camera retention policy (days). NULL means use global RETENTION_DAYS env var.
    op.add_column(
        'survapp_camera_master',
        sa.Column('retention_days', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('survapp_camera_master', 'retention_days')
    op.drop_index('ix_camera_status_log_camera_changed', table_name='camera_status_log')
    op.drop_table('camera_status_log')

"""Mobile devices

Revision ID: 0007_mobile_devices
Revises: 0006_edge_fleet
Create Date: 2026-07-06 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0007_mobile_devices'
down_revision: Union[str, None] = '0006_edge_fleet'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'mobile_device',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('survapp_user.id', ondelete="CASCADE"), nullable=False),
        sa.Column('device_token', sa.String(length=500), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('device_name', sa.String(length=200), nullable=True),
        sa.Column('app_version', sa.String(length=20), nullable=True),
        # Phase 16 -- WireGuard peer identity, added now so Stage C doesn't
        # need a second migration.
        sa.Column('wg_public_key', sa.String(length=200), nullable=True),
        sa.Column('wg_peer_id', sa.String(length=200), nullable=True),
        sa.Column('wg_peer_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('last_active', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_mobile_device_user_id', 'mobile_device', ['user_id'])
    op.create_index('ix_mobile_device_wg_peer_id', 'mobile_device', ['wg_peer_id'])


def downgrade() -> None:
    op.drop_index('ix_mobile_device_wg_peer_id', table_name='mobile_device')
    op.drop_index('ix_mobile_device_user_id', table_name='mobile_device')
    op.drop_table('mobile_device')
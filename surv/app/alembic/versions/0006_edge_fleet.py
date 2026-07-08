"""Edge NVR Fleet Migration

Revision ID: 0006_edge_fleet
Revises: 0005_camera_health
Create Date: 2026-07-06 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0006_edge_fleet'
down_revision: Union[str, None] = '0005_camera_health'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # nvr_node
    op.create_table(
        'nvr_node',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True, nullable=False),
        sa.Column('site_code', sa.String(length=50), nullable=False, unique=True),
        sa.Column('customer_site_id', sa.BigInteger(), sa.ForeignKey('customer_site.id'), nullable=True),
        sa.Column('overlay_ip', sa.String(length=50), nullable=True),
        sa.Column('wg_node_key', sa.String(length=200), nullable=True),
        sa.Column('hardware_label', sa.String(length=100), nullable=True),
        sa.Column('agent_version', sa.String(length=50), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disk_used_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('is_provisioned', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True)
    )

    # nvr_camera_map
    op.create_table(
        'nvr_camera_map',
        sa.Column('nvr_node_id', sa.Integer(), sa.ForeignKey('nvr_node.id'), primary_key=True, nullable=False),
        sa.Column('camera_id', sa.Integer(), sa.ForeignKey('survapp_camera_master.id'), primary_key=True, nullable=False)
    )

    # backup_clip
    op.create_table(
        'backup_clip',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True, nullable=False),
        sa.Column('nvr_node_id', sa.Integer(), sa.ForeignKey('nvr_node.id'), nullable=True),
        sa.Column('camera_id', sa.Integer(), sa.ForeignKey('survapp_camera_master.id'), nullable=True),
        sa.Column('object_key', sa.String(length=500), nullable=True),
        sa.Column('reason', sa.String(length=50), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True)
    )

    # Add nvr_node_id to survapp_camera_master
    op.add_column('survapp_camera_master', sa.Column('nvr_node_id', sa.Integer(), sa.ForeignKey('nvr_node.id'), nullable=True))


def downgrade() -> None:
    op.drop_column('survapp_camera_master', 'nvr_node_id')
    op.drop_table('backup_clip')
    op.drop_table('nvr_camera_map')
    op.drop_table('nvr_node')

"""BSNL Masters

Revision ID: 0004_bsnl_masters
Revises: 0003_company_hierarchy
Create Date: 2026-07-01 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_bsnl_masters'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create circle_master table
    op.create_table(
        'circle_master',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('cir_code', sa.String(length=50), nullable=False, unique=True),
        sa.Column('cir_name', sa.String(length=200), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    
    # 2. Create ba_master table
    op.create_table(
        'ba_master',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('ba_code', sa.String(length=50), nullable=False),
        sa.Column('ba_name', sa.String(length=200), nullable=False),
        sa.Column('circle_id', sa.BigInteger(), sa.ForeignKey('circle_master.id'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    # 3. Add foreign keys to organization
    op.add_column('organization', sa.Column('circle_id', sa.BigInteger(), nullable=True))
    op.add_column('organization', sa.Column('ba_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('fk_org_circle', 'organization', 'circle_master', ['circle_id'], ['id'])
    op.create_foreign_key('fk_org_ba', 'organization', 'ba_master', ['ba_id'], ['id'])

    # 4. Add foreign keys to customer
    op.add_column('customer', sa.Column('circle_id', sa.BigInteger(), nullable=True))
    op.add_column('customer', sa.Column('ba_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('fk_customer_circle', 'customer', 'circle_master', ['circle_id'], ['id'])
    op.create_foreign_key('fk_customer_ba', 'customer', 'ba_master', ['ba_id'], ['id'])

    # 5. Add foreign keys to survapp_user
    op.add_column('survapp_user', sa.Column('circle_id', sa.BigInteger(), nullable=True))
    op.add_column('survapp_user', sa.Column('ba_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('fk_user_circle', 'survapp_user', 'circle_master', ['circle_id'], ['id'])
    op.create_foreign_key('fk_user_ba', 'survapp_user', 'ba_master', ['ba_id'], ['id'])

    # 6. Add foreign keys to survapp_camera_master
    op.add_column('survapp_camera_master', sa.Column('circle_id', sa.BigInteger(), nullable=True))
    op.add_column('survapp_camera_master', sa.Column('ba_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('fk_camera_circle', 'survapp_camera_master', 'circle_master', ['circle_id'], ['id'])
    op.create_foreign_key('fk_camera_ba', 'survapp_camera_master', 'ba_master', ['ba_id'], ['id'])


def downgrade() -> None:
    # 6. Remove foreign keys from survapp_camera_master
    op.drop_constraint('fk_camera_ba', 'survapp_camera_master', type_='foreignkey')
    op.drop_constraint('fk_camera_circle', 'survapp_camera_master', type_='foreignkey')
    op.drop_column('survapp_camera_master', 'ba_id')
    op.drop_column('survapp_camera_master', 'circle_id')

    # 5. Remove foreign keys from survapp_user
    op.drop_constraint('fk_user_ba', 'survapp_user', type_='foreignkey')
    op.drop_constraint('fk_user_circle', 'survapp_user', type_='foreignkey')
    op.drop_column('survapp_user', 'ba_id')
    op.drop_column('survapp_user', 'circle_id')

    # 4. Remove foreign keys from customer
    op.drop_constraint('fk_customer_ba', 'customer', type_='foreignkey')
    op.drop_constraint('fk_customer_circle', 'customer', type_='foreignkey')
    op.drop_column('customer', 'ba_id')
    op.drop_column('customer', 'circle_id')

    # 3. Remove foreign keys from organization
    op.drop_constraint('fk_org_ba', 'organization', type_='foreignkey')
    op.drop_constraint('fk_org_circle', 'organization', type_='foreignkey')
    op.drop_column('organization', 'ba_id')
    op.drop_column('organization', 'circle_id')

    # 2. Drop ba_master
    op.drop_table('ba_master')

    # 1. Drop circle_master
    op.drop_table('circle_master')

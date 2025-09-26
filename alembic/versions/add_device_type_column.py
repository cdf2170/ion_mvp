"""add device_type column to devices table

Revision ID: add_device_type
Revises: c8bed965152a
Create Date: 2024-12-16 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_device_type'
down_revision = 'c8bed965152a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add device_type column to devices table
    op.add_column('devices', sa.Column('device_type', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove device_type column from devices table
    op.drop_column('devices', 'device_type')

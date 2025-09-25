"""add_performance_indexes

Revision ID: [auto-generated]
Revises: [previous revision]
Create Date: [auto-generated]

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '[auto-generated]'
down_revision = '[previous revision]'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Device table indexes for common searches
    op.create_index('idx_devices_name', 'devices', ['name'])
    op.create_index('idx_devices_owner_cid', 'devices', ['owner_cid'])
    op.create_index('idx_devices_status', 'devices', ['status'])
    op.create_index('idx_devices_compliant', 'devices', ['compliant'])
    op.create_index('idx_devices_ip_address', 'devices', ['ip_address'])
    op.create_index('idx_devices_last_seen', 'devices', ['last_seen'])
    
    # Device tags for filtering
    op.create_index('idx_device_tags_device_id', 'device_tags', ['device_id'])
    op.create_index('idx_device_tags_tag', 'device_tags', ['tag'])
    
    # Users for search
    op.create_index('idx_canonical_identities_email', 'canonical_identities', ['email'])
    op.create_index('idx_canonical_identities_full_name', 'canonical_identities', ['full_name'])
    op.create_index('idx_canonical_identities_department', 'canonical_identities', ['department'])

def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_devices_name')
    op.drop_index('idx_devices_owner_cid')
    op.drop_index('idx_devices_status')
    op.drop_index('idx_devices_compliant')
    op.drop_index('idx_devices_ip_address')
    op.drop_index('idx_devices_last_seen')
    op.drop_index('idx_device_tags_device_id')
    op.drop_index('idx_device_tags_tag')
    op.drop_index('idx_canonical_identities_email')
    op.drop_index('idx_canonical_identities_full_name')
    op.drop_index('idx_canonical_identities_department')

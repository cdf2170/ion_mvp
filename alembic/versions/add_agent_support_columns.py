"""Add agent support columns to devices table

Revision ID: agent_support_cols
Revises: 0089593d7775
Create Date: 2025-09-23 19:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'agent_support_cols'
down_revision = '0089593d7775'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create AgentStatusEnum if it doesn't exist
    agent_status_enum = postgresql.ENUM(
        'INSTALLED', 'RUNNING', 'STOPPED', 'ERROR', 'UPDATING', 'UNINSTALLED',
        name='agentstatusenum'
    )
    agent_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Add agent columns to devices table
    op.add_column('devices', sa.Column('agent_installed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('devices', sa.Column('agent_version', sa.String(), nullable=True))
    op.add_column('devices', sa.Column('agent_status', agent_status_enum, nullable=True))
    op.add_column('devices', sa.Column('agent_last_checkin', sa.DateTime(timezone=True), nullable=True))
    op.add_column('devices', sa.Column('agent_config_hash', sa.String(), nullable=True))
    op.add_column('devices', sa.Column('agent_data', sa.JSON(), nullable=True))
    op.add_column('devices', sa.Column('hardware_uuid', sa.String(), nullable=True))
    op.add_column('devices', sa.Column('motherboard_serial', sa.String(), nullable=True))
    op.add_column('devices', sa.Column('cpu_id', sa.String(), nullable=True))
    
    # Create agent_events table
    op.create_table('agent_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('device_id', sa.UUID(), nullable=False),
        sa.Column('event_type', postgresql.ENUM(
            'USER_LOGIN', 'USER_LOGOUT', 'PROCESS_START', 'PROCESS_STOP', 
            'NETWORK_CONNECTION', 'USB_DEVICE_CONNECTED', 'USB_DEVICE_DISCONNECTED',
            'SERVICE_START', 'SERVICE_STOP', 'REGISTRY_CHANGE', 'FILE_ACCESS',
            'SECURITY_EVENT', 'SYSTEM_BOOT', 'SYSTEM_SHUTDOWN', 'ERROR',
            name='agenteventtypeenum', create_type=True
        ), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=False),
        sa.Column('user_context', sa.String(), nullable=True),
        sa.Column('risk_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correlation_id', sa.String(), nullable=True),
        sa.Column('parent_event_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_event_id'], ['agent_events.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('risk_score >= 0 AND risk_score <= 100')
    )


def downgrade() -> None:
    # Remove agent_events table
    op.drop_table('agent_events')
    
    # Remove agent columns from devices table
    op.drop_column('devices', 'cpu_id')
    op.drop_column('devices', 'motherboard_serial')
    op.drop_column('devices', 'hardware_uuid')
    op.drop_column('devices', 'agent_data')
    op.drop_column('devices', 'agent_config_hash')
    op.drop_column('devices', 'agent_last_checkin')
    op.drop_column('devices', 'agent_status')
    op.drop_column('devices', 'agent_version')
    op.drop_column('devices', 'agent_installed')
    
    # Drop enums
    sa.Enum(name='agenteventtypeenum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='agentstatusenum').drop(op.get_bind(), checkfirst=True)

"""Add agent support to devices and create agent events table

Revision ID: add_agent_support
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_agent_support'
down_revision = None  # Update this to your latest revision
branch_labels = None
depends_on = None


def upgrade():
    # Create agent status enum
    agent_status_enum = postgresql.ENUM(
        'INSTALLED', 'RUNNING', 'STOPPED', 'ERROR', 'UPDATING', 'UNINSTALLED',
        name='agentstatusenum'
    )
    agent_status_enum.create(op.get_bind())

    # Create agent event type enum
    agent_event_type_enum = postgresql.ENUM(
        'LOGIN', 'LOGOUT', 'PROCESS_START', 'PROCESS_END', 'NETWORK_CONNECTION',
        'FILE_ACCESS', 'USB_CONNECT', 'USB_DISCONNECT', 'SOFTWARE_INSTALL',
        'SOFTWARE_UNINSTALL', 'REGISTRY_CHANGE', 'SERVICE_START', 'SERVICE_STOP',
        'CERTIFICATE_USE', 'POLICY_VIOLATION', 'HEARTBEAT',
        name='agenteventtypeenum'
    )
    agent_event_type_enum.create(op.get_bind())

    # Add agent-specific columns to devices table
    op.add_column('devices', sa.Column('agent_installed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('devices', sa.Column('agent_version', sa.String(), nullable=True))
    op.add_column('devices', sa.Column('agent_status', agent_status_enum, nullable=True))
    op.add_column('devices', sa.Column('agent_last_checkin', sa.DateTime(timezone=True), nullable=True))
    op.add_column('devices', sa.Column('agent_config_hash', sa.String(), nullable=True))
    
    # Add hardware fingerprinting columns
    op.add_column('devices', sa.Column('hardware_uuid', sa.String(), nullable=True))
    op.add_column('devices', sa.Column('motherboard_serial', sa.String(), nullable=True))
    op.add_column('devices', sa.Column('cpu_id', sa.String(), nullable=True))
    
    # Add agent data JSON column
    op.add_column('devices', sa.Column('agent_data', sa.JSON(), nullable=True))

    # Create agent_events table
    op.create_table('agent_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('devices.id'), nullable=False),
        sa.Column('event_type', agent_event_type_enum, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('event_data', sa.JSON(), nullable=False),
        sa.Column('user_context', sa.String(), nullable=True),
        sa.Column('risk_score', sa.Integer(), default=0),
        sa.Column('correlation_id', sa.String(), nullable=True),
        sa.Column('parent_event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_events.id'), nullable=True)
    )

    # Create indexes for better performance
    op.create_index('idx_devices_hardware_uuid', 'devices', ['hardware_uuid'])
    op.create_index('idx_devices_motherboard_serial', 'devices', ['motherboard_serial'])
    op.create_index('idx_devices_agent_status', 'devices', ['agent_status'])
    op.create_index('idx_agent_events_device_id', 'agent_events', ['device_id'])
    op.create_index('idx_agent_events_timestamp', 'agent_events', ['timestamp'])
    op.create_index('idx_agent_events_event_type', 'agent_events', ['event_type'])
    op.create_index('idx_agent_events_correlation_id', 'agent_events', ['correlation_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_agent_events_correlation_id')
    op.drop_index('idx_agent_events_event_type')
    op.drop_index('idx_agent_events_timestamp')
    op.drop_index('idx_agent_events_device_id')
    op.drop_index('idx_devices_agent_status')
    op.drop_index('idx_devices_motherboard_serial')
    op.drop_index('idx_devices_hardware_uuid')

    # Drop agent_events table
    op.drop_table('agent_events')

    # Remove agent columns from devices table
    op.drop_column('devices', 'agent_data')
    op.drop_column('devices', 'cpu_id')
    op.drop_column('devices', 'motherboard_serial')
    op.drop_column('devices', 'hardware_uuid')
    op.drop_column('devices', 'agent_config_hash')
    op.drop_column('devices', 'agent_last_checkin')
    op.drop_column('devices', 'agent_status')
    op.drop_column('devices', 'agent_version')
    op.drop_column('devices', 'agent_installed')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS agenteventtypeenum')
    op.execute('DROP TYPE IF EXISTS agentstatusenum')

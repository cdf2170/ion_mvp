#!/usr/bin/env python3
"""
Run agent support migration on Railway
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def run_migration():
    """Run the agent support migration manually"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Create AgentStatusEnum if it doesn't exist
            print("Creating AgentStatusEnum...")
            conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE agentstatusenum AS ENUM ('INSTALLED', 'RUNNING', 'STOPPED', 'ERROR', 'UPDATING', 'UNINSTALLED');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            # Create AgentEventTypeEnum if it doesn't exist
            print("Creating AgentEventTypeEnum...")
            conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE agenteventtypeenum AS ENUM (
                        'USER_LOGIN', 'USER_LOGOUT', 'PROCESS_START', 'PROCESS_STOP', 
                        'NETWORK_CONNECTION', 'USB_DEVICE_CONNECTED', 'USB_DEVICE_DISCONNECTED',
                        'SERVICE_START', 'SERVICE_STOP', 'REGISTRY_CHANGE', 'FILE_ACCESS',
                        'SECURITY_EVENT', 'SYSTEM_BOOT', 'SYSTEM_SHUTDOWN', 'ERROR'
                    );
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            # Add agent columns to devices table if they don't exist
            print("Adding agent columns to devices table...")
            
            agent_columns = [
                "ALTER TABLE devices ADD COLUMN IF NOT EXISTS agent_installed BOOLEAN NOT NULL DEFAULT false",
                "ALTER TABLE devices ADD COLUMN IF NOT EXISTS agent_version VARCHAR",
                "ALTER TABLE devices ADD COLUMN IF NOT EXISTS agent_status agentstatusenum",
                "ALTER TABLE devices ADD COLUMN IF NOT EXISTS agent_last_checkin TIMESTAMP WITH TIME ZONE",
                "ALTER TABLE devices ADD COLUMN IF NOT EXISTS agent_config_hash VARCHAR",
                "ALTER TABLE devices ADD COLUMN IF NOT EXISTS agent_data JSON",
                "ALTER TABLE devices ADD COLUMN IF NOT EXISTS hardware_uuid VARCHAR",
                "ALTER TABLE devices ADD COLUMN IF NOT EXISTS motherboard_serial VARCHAR",
                "ALTER TABLE devices ADD COLUMN IF NOT EXISTS cpu_id VARCHAR"
            ]
            
            for column_sql in agent_columns:
                try:
                    conn.execute(text(column_sql))
                    print(f"   {column_sql}")
                except Exception as e:
                    print(f"  ⚠ Warning: {column_sql} - {e}")
            
            # Create agent_events table if it doesn't exist
            print("Creating agent_events table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agent_events (
                    id UUID PRIMARY KEY,
                    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
                    event_type agenteventtypeenum NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    event_data JSON NOT NULL,
                    user_context VARCHAR,
                    risk_score INTEGER NOT NULL DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
                    correlation_id VARCHAR,
                    parent_event_id UUID REFERENCES agent_events(id)
                )
            """))
            
            # Commit all changes
            conn.commit()
            print(" Agent support migration completed successfully!")
            return True
            
    except Exception as e:
        print(f" Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

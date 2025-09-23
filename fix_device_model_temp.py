#!/usr/bin/env python3
"""
Temporary fix to remove agent columns from Device model for seeding
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def create_temp_device_model():
    """Create a temporary device model without agent columns"""
    
    model_file = project_root / "backend" / "app" / "db" / "models.py"
    
    # Read the current models.py
    with open(model_file, 'r') as f:
        content = f.read()
    
    # Comment out agent columns temporarily
    agent_columns = [
        "agent_installed = Column(Boolean, nullable=False, default=False)",
        "agent_version = Column(String)",
        "agent_status = Column(SQLEnum(AgentStatusEnum))",
        "agent_last_checkin = Column(DateTime(timezone=True))",
        "agent_config_hash = Column(String)",
        "hardware_uuid = Column(String)",
        "motherboard_serial = Column(String)",
        "cpu_id = Column(String)",
        "agent_data = Column(JSON)",
        'agent_events = relationship("AgentEvent", back_populates="device", cascade="all, delete-orphan")'
    ]
    
    for column in agent_columns:
        content = content.replace(column, f"# TEMP_COMMENTED: {column}")
    
    # Write the modified content
    with open(model_file, 'w') as f:
        f.write(content)
    
    print("Temporarily commented out agent columns in Device model")

def restore_device_model():
    """Restore the original device model with agent columns"""
    
    model_file = project_root / "backend" / "app" / "db" / "models.py"
    
    # Read the current models.py
    with open(model_file, 'r') as f:
        content = f.read()
    
    # Uncomment agent columns
    content = content.replace("# TEMP_COMMENTED: ", "")
    
    # Write the restored content
    with open(model_file, 'w') as f:
        f.write(content)
    
    print("Restored agent columns in Device model")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_device_model()
    else:
        create_temp_device_model()

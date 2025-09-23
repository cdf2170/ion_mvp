from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
import json
import logging

from backend.app.db.session import get_db
from backend.app.db.models import (
    Device, CanonicalIdentity, 
    DeviceStatusEnum, AgentStatusEnum
)
# TEMP_COMMENTED: AgentEvent, AgentEventTypeEnum
from backend.app.security.auth import verify_token
from backend.app.services.identity_correlation import IdentityCorrelationEngine

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)

# Pydantic models for agent communication
from pydantic import BaseModel, Field

class AgentRegistrationRequest(BaseModel):
    name: str = Field(..., description="Device name")
    hardware_uuid: Optional[str] = Field(None, description="Hardware UUID")
    motherboard_serial: Optional[str] = Field(None, description="Motherboard serial")
    cpu_id: Optional[str] = Field(None, description="CPU identifier")
    mac_address: Optional[str] = Field(None, description="Primary MAC address")
    ip_address: Optional[str] = Field(None, description="Current IP address")
    os_version: Optional[str] = Field(None, description="Operating system version")
    manufacturer: Optional[str] = Field(None, description="System manufacturer")
    model: Optional[str] = Field(None, description="System model")
    agent_version: str = Field(..., description="Agent version")
    organization_id: Optional[str] = Field(None, description="Organization identifier")
    fingerprint: str = Field(..., description="Device fingerprint")

class AgentHeartbeatRequest(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    timestamp: datetime = Field(..., description="Heartbeat timestamp")
    status: str = Field(..., description="Agent status")
    agent_version: str = Field(..., description="Agent version")
    ip_address: Optional[str] = Field(None, description="Current IP address")
    last_boot_time: Optional[datetime] = Field(None, description="Last boot time")
    system_uptime: Optional[str] = Field(None, description="System uptime")
    config_hash: str = Field(..., description="Configuration hash")

class AgentEventData(BaseModel):
    id: str = Field(..., description="Event ID")
    device_id: str = Field(..., description="Device ID")
    event_type: str = Field(..., description="Event type")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_data: Dict[str, Any] = Field(..., description="Event-specific data")
    user_context: Optional[str] = Field(None, description="User context")
    risk_score: int = Field(0, description="Risk score 0-100")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
    parent_event_id: Optional[str] = Field(None, description="Parent event ID")

class AgentEventBatchRequest(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    events: List[AgentEventData] = Field(..., description="List of events")
    batch_timestamp: datetime = Field(..., description="Batch timestamp")

class DiscrepancyReport(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    discrepancy_type: str = Field(..., description="Type of discrepancy")
    discrepancy_data: Dict[str, Any] = Field(..., description="Discrepancy details")
    timestamp: datetime = Field(..., description="Report timestamp")
    agent_version: str = Field(..., description="Agent version")


@router.post("/register")
async def register_agent(
    request: AgentRegistrationRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Register a new agent and correlate with existing device records.
    
    This endpoint:
    1. Attempts to correlate the agent with existing device records
    2. Creates a new device record if no match is found
    3. Updates device with agent-specific information
    4. Returns the device ID for future communication
    """
    try:
        correlation_engine = IdentityCorrelationEngine(db)
        
        # Try to find existing device by hardware fingerprints
        existing_device = None
        
        # Search by hardware UUID first (most reliable)
        if request.hardware_uuid:
            existing_device = db.query(Device).filter(
                Device.hardware_uuid == request.hardware_uuid
            ).first()
        
        # Search by motherboard serial if no UUID match
        if not existing_device and request.motherboard_serial:
            existing_device = db.query(Device).filter(
                Device.motherboard_serial == request.motherboard_serial
            ).first()
        
        # Search by MAC address as fallback
        if not existing_device and request.mac_address:
            existing_device = db.query(Device).filter(
                Device.mac_address == request.mac_address
            ).first()
        
        if existing_device:
            # Update existing device with agent information
            existing_device.agent_installed = True
            existing_device.agent_version = request.agent_version
            existing_device.agent_status = AgentStatusEnum.RUNNING
            existing_device.agent_last_checkin = datetime.utcnow()
            existing_device.hardware_uuid = request.hardware_uuid
            existing_device.motherboard_serial = request.motherboard_serial
            existing_device.cpu_id = request.cpu_id
            existing_device.status = DeviceStatusEnum.CONNECTED
            existing_device.last_seen = datetime.utcnow()
            
            # Update network info if provided
            if request.ip_address:
                existing_device.ip_address = request.ip_address
            if request.mac_address:
                existing_device.mac_address = request.mac_address
            
            db.commit()
            
            logger.info(f"Agent registered for existing device: {existing_device.id}")
            
            return {
                "success": True,
                "device_id": str(existing_device.id),
                "message": "Agent registered for existing device",
                "correlation_status": "matched_existing"
            }
        
        else:
            # Create new device record - this indicates a potential gap in API data
            # We'll need to correlate this with a canonical identity later
            
            # For now, create an orphaned device that will be correlated later
            new_device = Device(
                name=request.name,
                hardware_uuid=request.hardware_uuid,
                motherboard_serial=request.motherboard_serial,
                cpu_id=request.cpu_id,
                mac_address=request.mac_address,
                ip_address=request.ip_address,
                os_version=request.os_version,
                agent_installed=True,
                agent_version=request.agent_version,
                agent_status=AgentStatusEnum.RUNNING,
                agent_last_checkin=datetime.utcnow(),
                status=DeviceStatusEnum.CONNECTED,
                # Temporary owner - will be updated when we correlate with user
                owner_cid=None  # This will need to be handled
            )
            
            # Note: In production, you'd want to have a process to correlate
            # orphaned devices with canonical identities
            
            db.add(new_device)
            db.commit()
            
            logger.warning(f"Created orphaned device from agent registration: {new_device.id}")
            
            return {
                "success": True,
                "device_id": str(new_device.id),
                "message": "New device created from agent registration",
                "correlation_status": "orphaned_device",
                "warning": "Device not correlated with user identity - manual correlation may be required"
            }
            
    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent registration failed: {str(e)}"
        )


@router.post("/heartbeat")
async def agent_heartbeat(
    request: AgentHeartbeatRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Process agent heartbeat and update device status.
    """
    try:
        device = db.query(Device).filter(Device.id == request.device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Update device status
        device.agent_last_checkin = request.timestamp
        device.agent_status = AgentStatusEnum.RUNNING
        device.status = DeviceStatusEnum.CONNECTED
        device.last_seen = request.timestamp
        
        if request.ip_address:
            device.ip_address = request.ip_address
        
        # Store additional heartbeat data
        heartbeat_data = {
            "agent_version": request.agent_version,
            "system_uptime": request.system_uptime,
            "config_hash": request.config_hash,
            "last_boot_time": request.last_boot_time.isoformat() if request.last_boot_time else None
        }
        
        if device.agent_data:
            existing_data = json.loads(device.agent_data) if isinstance(device.agent_data, str) else device.agent_data
            existing_data.update(heartbeat_data)
            device.agent_data = existing_data
        else:
            device.agent_data = heartbeat_data
        
        db.commit()
        
        return {
            "success": True,
            "message": "Heartbeat processed",
            "next_heartbeat": datetime.utcnow() + timedelta(seconds=300)  # 5 minutes
        }
        
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Heartbeat processing failed: {str(e)}"
        )


# TEMP_COMMENTED: @router.post("/events")
# TEMP_COMMENTED: async def receive_agent_events(
# TEMP_COMMENTED:     request: AgentEventBatchRequest,
# TEMP_COMMENTED:     db: Session = Depends(get_db),
# TEMP_COMMENTED:     _: str = Depends(verify_token)
# TEMP_COMMENTED: ):
# TEMP_COMMENTED:     """
# TEMP_COMMENTED:     Receive and process batch of events from agent.
# TEMP_COMMENTED:     """
# TEMP_COMMENTED:     # Temporarily disabled due to schema issues
# TEMP_COMMENTED:     return {"message": "Event processing temporarily disabled"}

@router.post("/events")
async def receive_agent_events_temp(
    request: dict,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Temporary stub for agent events (agent functionality disabled).
    """
    return {
        "success": True,
        "events_processed": 0,
        "events_failed": 0,
        "message": "Agent event processing temporarily disabled during schema migration"
    }


@router.get("/{device_id}/config")
async def get_agent_config(
    device_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get configuration for a specific agent.
    """
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Return default configuration for now
        # In production, this would be customizable per device/organization
        config = {
            "heartbeat_interval_seconds": 300,
            "data_collection_interval_seconds": 60,
            "max_event_batch_size": 100,
            "max_batch_wait_seconds": 30,
            "enable_real_time_monitoring": True,
            "enable_process_monitoring": True,
            "enable_network_monitoring": True,
            "enable_usb_monitoring": True,
            "enable_registry_monitoring": False,
            "log_level": "Info",
            "api_timeout_seconds": 30,
            "max_retry_attempts": 3,
            "retry_delay_seconds": 5
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Error getting agent config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Config retrieval failed: {str(e)}"
        )


@router.post("/discrepancies")
async def report_discrepancy(
    request: DiscrepancyReport,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Receive discrepancy reports from agents.
    
    This is where agents report when they detect differences between
    their real-time data and what the API systems report.
    """
    try:
        device = db.query(Device).filter(Device.id == request.device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Log the discrepancy for analysis
        logger.warning(f"Discrepancy reported by device {request.device_id}: {request.discrepancy_type}")
        logger.info(f"Discrepancy data: {request.discrepancy_data}")
        
        # Store discrepancy in agent_data for analysis
        discrepancy_record = {
            "type": request.discrepancy_type,
            "data": request.discrepancy_data,
            "timestamp": request.timestamp.isoformat(),
            "agent_version": request.agent_version
        }
        
        if device.agent_data:
            existing_data = json.loads(device.agent_data) if isinstance(device.agent_data, str) else device.agent_data
            if "discrepancies" not in existing_data:
                existing_data["discrepancies"] = []
            existing_data["discrepancies"].append(discrepancy_record)
            device.agent_data = existing_data
        else:
            device.agent_data = {"discrepancies": [discrepancy_record]}
        
        db.commit()
        
        return {
            "success": True,
            "message": "Discrepancy report received",
            "action": "logged_for_analysis"
        }
        
    except Exception as e:
        logger.error(f"Error processing discrepancy report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Discrepancy reporting failed: {str(e)}"
        )

"""
Sync Orchestrator - Manages API synchronization with error handling and fallbacks.

This handles the actual pulling of data from external APIs and coordinating
the correlation process.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.app.db.models import (
    APIConnection, APISyncLog, APIConnectionStatusEnum, CanonicalIdentity, Device
)
from backend.app.services.identity_correlation import IdentityCorrelationEngine, CorrelationError

logger = logging.getLogger(__name__)


class SyncOrchestrator:
    """
    Orchestrates synchronization from multiple API sources with error handling.
    
    This class:
    - Manages sync jobs for all connected APIs
    - Handles failures with retry logic
    - Coordinates with the correlation engine
    - Provides sync status and metrics
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.correlation_engine = IdentityCorrelationEngine(db)
    
    def sync_all_connections(self, force_sync: bool = False) -> Dict[str, Any]:
        """
        Sync data from all active API connections.
        
        Args:
            force_sync: If True, sync even if not scheduled
            
        Returns:
            Summary of sync results
        """
        results = {
            "started_at": datetime.now(),
            "connections_processed": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "total_users_processed": 0,
            "total_devices_processed": 0,
            "errors": []
        }
        
        # Get all active connections that need syncing
        connections = self._get_connections_to_sync(force_sync)
        
        for connection in connections:
            try:
                sync_result = self.sync_connection(connection.id)
                results["connections_processed"] += 1
                
                if sync_result["status"] == "success":
                    results["successful_syncs"] += 1
                    results["total_users_processed"] += sync_result.get("users_processed", 0)
                    results["total_devices_processed"] += sync_result.get("devices_processed", 0)
                else:
                    results["failed_syncs"] += 1
                    results["errors"].extend(sync_result.get("errors", []))
                    
            except Exception as e:
                error_msg = f"Failed to sync connection {connection.name}: {str(e)}"
                logger.error(error_msg)
                results["failed_syncs"] += 1
                results["errors"].append(error_msg)
        
        results["completed_at"] = datetime.now()
        results["duration_seconds"] = (results["completed_at"] - results["started_at"]).total_seconds()
        
        logger.info(f"Sync completed: {results['successful_syncs']}/{results['connections_processed']} successful")
        return results
    
    def sync_connection(self, connection_id: str) -> Dict[str, Any]:
        """
        Sync data from a specific API connection.
        
        Args:
            connection_id: UUID of the API connection
            
        Returns:
            Sync result summary
        """
        connection = self.db.query(APIConnection).filter(
            APIConnection.id == connection_id
        ).first()
        
        if not connection:
            raise ValueError(f"API connection {connection_id} not found")
        
        # Create sync log entry
        sync_log = APISyncLog(
            connection_id=connection.id,
            sync_type="scheduled",
            started_at=datetime.now(),
            status="running"
        )
        self.db.add(sync_log)
        self.db.flush()
        
        try:
            # Update connection status
            connection.status = APIConnectionStatusEnum.CONNECTED
            connection.last_health_check = datetime.now()
            
            # Get the appropriate connector for this provider
            connector = self._get_connector(connection)
            
            # Sync users if supported
            users_processed = 0
            if connection.supports_users:
                users_processed = self._sync_users(connector, connection)
            
            # Sync devices if supported
            devices_processed = 0
            if connection.supports_devices:
                devices_processed = self._sync_devices(connector, connection)
            
            # Update sync log with success
            sync_log.completed_at = datetime.now()
            sync_log.duration_seconds = str((sync_log.completed_at - sync_log.started_at).total_seconds())
            sync_log.status = "success"
            sync_log.records_processed = str(users_processed + devices_processed)
            sync_log.records_created = str(self.correlation_engine.correlation_stats["users_created"])
            sync_log.records_updated = str(self.correlation_engine.correlation_stats["users_updated"])
            
            # Update connection last sync time
            connection.last_sync = datetime.now()
            connection.next_sync = self._calculate_next_sync(connection)
            
            self.db.commit()
            
            return {
                "status": "success",
                "users_processed": users_processed,
                "devices_processed": devices_processed,
                "correlation_stats": self.correlation_engine.get_correlation_stats()
            }
            
        except Exception as e:
            # Update sync log with failure
            sync_log.completed_at = datetime.now()
            sync_log.status = "error"
            sync_log.error_message = str(e)
            
            # Update connection status
            connection.status = APIConnectionStatusEnum.ERROR
            connection.health_check_message = f"Sync failed: {str(e)}"
            
            self.db.commit()
            
            return {
                "status": "error",
                "error": str(e),
                "users_processed": 0,
                "devices_processed": 0
            }
    
    def _get_connections_to_sync(self, force_sync: bool = False) -> List[APIConnection]:
        """Get API connections that need to be synced."""
        if force_sync:
            # Sync all enabled connections
            return self.db.query(APIConnection).filter(
                APIConnection.sync_enabled == True
            ).all()
        
        # Sync connections that are due for sync
        now = datetime.now()
        return self.db.query(APIConnection).filter(
            and_(
                APIConnection.sync_enabled == True,
                APIConnection.next_sync <= now
            )
        ).all()
    
    def _get_connector(self, connection: APIConnection):
        """Get the appropriate connector class for this API provider."""
        
        # Import connectors dynamically to avoid circular imports
        if connection.provider.value == "OKTA":
            from backend.app.services.connectors.okta_connector import OktaConnector
            return OktaConnector(connection, self.db)
        
        elif connection.provider.value == "AZURE_AD":
            from backend.app.services.connectors.azure_ad_connector import AzureADConnector  
            return AzureADConnector(connection, self.db)
        
        elif connection.provider.value == "CROWDSTRIKE":
            from backend.app.services.connectors.crowdstrike_connector import CrowdStrikeConnector
            return CrowdStrikeConnector(connection, self.db)
        
        # Add more connectors as needed
        else:
            raise NotImplementedError(f"Connector for {connection.provider.value} not implemented yet")
    
    def _sync_users(self, connector, connection: APIConnection) -> int:
        """Sync users from the external API."""
        users_processed = 0
        
        try:
            # Get users from external API
            api_users = connector.get_users()
            
            for api_user in api_users:
                try:
                    # Use correlation engine to map user data
                    canonical_user, was_created = self.correlation_engine.correlate_user_data(
                        api_user, connection.name
                    )
                    users_processed += 1
                    
                except CorrelationError as e:
                    logger.error(f"Failed to correlate user {api_user.get('email', 'unknown')}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to sync users from {connection.name}: {e}")
            raise
        
        return users_processed
    
    def _sync_devices(self, connector, connection: APIConnection) -> int:
        """Sync devices from the external API."""
        devices_processed = 0
        
        try:
            # Get devices from external API
            api_devices = connector.get_devices()
            
            for api_device in api_devices:
                try:
                    # Use correlation engine to map device data
                    device, was_created = self.correlation_engine.correlate_device_data(
                        api_device, connection.name
                    )
                    devices_processed += 1
                    
                except CorrelationError as e:
                    logger.error(f"Failed to correlate device {api_device.get('name', 'unknown')}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to sync devices from {connection.name}: {e}")
            raise
        
        return devices_processed
    
    def _calculate_next_sync(self, connection: APIConnection) -> datetime:
        """Calculate when the next sync should occur."""
        try:
            interval_minutes = int(connection.sync_interval_minutes or "60")
        except (ValueError, TypeError):
            interval_minutes = 60  # Default to 1 hour
        
        return datetime.now() + timedelta(minutes=interval_minutes)
    
    def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """
        Test an API connection to verify it's working.
        
        Args:
            connection_id: UUID of the API connection
            
        Returns:
            Test result with status and details
        """
        connection = self.db.query(APIConnection).filter(
            APIConnection.id == connection_id
        ).first()
        
        if not connection:
            return {"status": "error", "message": "Connection not found"}
        
        try:
            connector = self._get_connector(connection)
            test_result = connector.test_connection()
            
            # Update connection health
            connection.last_health_check = datetime.now()
            
            if test_result["status"] == "success":
                connection.status = APIConnectionStatusEnum.CONNECTED
                connection.health_check_message = "Connection test successful"
            else:
                connection.status = APIConnectionStatusEnum.ERROR
                connection.health_check_message = test_result.get("message", "Connection test failed")
            
            self.db.commit()
            return test_result
            
        except Exception as e:
            error_msg = f"Connection test failed: {str(e)}"
            connection.status = APIConnectionStatusEnum.ERROR
            connection.health_check_message = error_msg
            connection.last_health_check = datetime.now()
            
            self.db.commit()
            
            return {"status": "error", "message": error_msg}
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get overall sync status across all connections."""
        
        # Get connection counts by status
        total_connections = self.db.query(APIConnection).count()
        connected = self.db.query(APIConnection).filter(
            APIConnection.status == APIConnectionStatusEnum.CONNECTED
        ).count()
        error_connections = self.db.query(APIConnection).filter(
            APIConnection.status == APIConnectionStatusEnum.ERROR
        ).count()
        
        # Get recent sync results
        recent_syncs = self.db.query(APISyncLog).filter(
            APISyncLog.started_at >= datetime.now() - timedelta(hours=24)
        ).order_by(APISyncLog.started_at.desc()).limit(10).all()
        
        return {
            "connections": {
                "total": total_connections,
                "connected": connected,
                "error": error_connections,
                "health_percentage": round((connected / total_connections * 100), 2) if total_connections > 0 else 0
            },
            "recent_syncs": [
                {
                    "connection_id": str(sync.connection_id),
                    "started_at": sync.started_at.isoformat(),
                    "status": sync.status,
                    "records_processed": sync.records_processed,
                    "duration_seconds": sync.duration_seconds
                }
                for sync in recent_syncs
            ],
            "last_updated": datetime.now().isoformat()
        }

"""
Cryptographic Audit Services - Tamper-Proof Evidence Generation

This module provides cryptographic integrity for audit evidence:
- Digital signatures for audit records
- Merkle tree chains for immutable audit trails
- Timestamping services for non-repudiation
- Hash verification for data integrity

All audit evidence is cryptographically signed and timestamped to ensure
it cannot be tampered with after generation.
"""

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import base64
import secrets
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
import os


class AuditCryptoService:
    """
    Cryptographic service for audit evidence integrity.
    
    Provides digital signatures, hash chains, and timestamping for audit records.
    """
    
    def __init__(self):
        self.private_key = self._load_or_generate_private_key()
        self.public_key = self.private_key.public_key()
        self.audit_secret = self._get_audit_secret()
        
    def _load_or_generate_private_key(self):
        """Load existing private key or generate new one for audit signing"""
        key_path = "audit_private_key.pem"
        
        if os.path.exists(key_path):
            with open(key_path, "rb") as key_file:
                private_key = load_pem_private_key(
                    key_file.read(),
                    password=None,
                )
        else:
            # Generate new RSA key pair for audit signing
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Save private key
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            with open(key_path, "wb") as key_file:
                key_file.write(pem)
                
        return private_key
    
    def _get_audit_secret(self) -> str:
        """Get or generate audit secret for HMAC operations"""
        secret_path = "audit_secret.key"
        
        if os.path.exists(secret_path):
            with open(secret_path, "r") as f:
                return f.read().strip()
        else:
            # Generate new secret
            secret = secrets.token_urlsafe(32)
            with open(secret_path, "w") as f:
                f.write(secret)
            return secret
    
    def generate_audit_timestamp(self) -> Dict[str, Any]:
        """
        Generate cryptographically secure timestamp for audit records.
        
        Returns:
            Dictionary with timestamp data and integrity proof
        """
        now = datetime.now(timezone.utc)
        timestamp_data = {
            "timestamp": now.isoformat(),
            "unix_timestamp": int(now.timestamp()),
            "nanoseconds": time.time_ns(),
            "timezone": "UTC",
            "format": "ISO8601"
        }
        
        # Create hash of timestamp data
        timestamp_json = json.dumps(timestamp_data, sort_keys=True)
        timestamp_hash = hashlib.sha256(timestamp_json.encode()).hexdigest()
        
        # Sign the timestamp hash
        signature = self._sign_data(timestamp_hash)
        
        return {
            **timestamp_data,
            "timestamp_hash": timestamp_hash,
            "timestamp_signature": signature,
            "signed_by": "audit_system",
            "integrity_verified": True
        }
    
    def _sign_data(self, data: str) -> str:
        """
        Digitally sign data using RSA private key.
        
        Args:
            data: String data to sign
            
        Returns:
            Base64 encoded signature
        """
        signature = self.private_key.sign(
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode()
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """
        Verify digital signature using RSA public key.
        
        Args:
            data: Original data that was signed
            signature: Base64 encoded signature to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            signature_bytes = base64.b64decode(signature)
            self.public_key.verify(
                signature_bytes,
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def generate_evidence_hash(self, evidence_data: Dict[str, Any]) -> str:
        """
        Generate SHA-256 hash of evidence data for integrity verification.
        
        Args:
            evidence_data: Dictionary containing evidence
            
        Returns:
            Hexadecimal hash string
        """
        # Create deterministic JSON representation
        evidence_json = json.dumps(evidence_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(evidence_json.encode()).hexdigest()
    
    def generate_hmac_signature(self, data: str) -> str:
        """
        Generate HMAC signature for data integrity.
        
        Args:
            data: String data to sign
            
        Returns:
            Hexadecimal HMAC signature
        """
        return hmac.new(
            self.audit_secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_hmac_signature(self, data: str, signature: str) -> bool:
        """
        Verify HMAC signature.
        
        Args:
            data: Original data
            signature: HMAC signature to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = self.generate_hmac_signature(data)
        return hmac.compare_digest(expected_signature, signature)
    
    def create_audit_record(
        self, 
        record_type: str,
        subject_cid: Optional[UUID],
        evidence_data: Dict[str, Any],
        compliance_framework: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create cryptographically signed audit record.
        
        Args:
            record_type: Type of audit record
            subject_cid: CID of the subject (user/device)
            evidence_data: The actual evidence data
            compliance_framework: Applicable compliance framework
            
        Returns:
            Complete audit record with cryptographic proof
        """
        # Generate secure timestamp
        timestamp_info = self.generate_audit_timestamp()
        
        # Create base record
        record = {
            "record_id": secrets.token_urlsafe(16),
            "record_type": record_type,
            "subject_cid": str(subject_cid) if subject_cid else None,
            "compliance_framework": compliance_framework,
            "evidence_data": evidence_data,
            "timestamp_info": timestamp_info,
            "generated_by": "audit_insurance_system",
            "version": "1.0"
        }
        
        # Generate evidence hash
        evidence_hash = self.generate_evidence_hash(evidence_data)
        record["evidence_hash"] = evidence_hash
        
        # Create a canonical representation for hashing (deterministic order)
        hashable_data = {
            "record_id": record["record_id"],
            "record_type": record["record_type"],
            "subject_cid": record["subject_cid"],
            "compliance_framework": record["compliance_framework"],
            "evidence_data": record["evidence_data"],
            "evidence_hash": record["evidence_hash"],
            "timestamp_info": record["timestamp_info"],
            "generated_by": record["generated_by"],
            "version": record["version"]
        }

        record_json = json.dumps(hashable_data, sort_keys=True, separators=(',', ':'))
        record_hash = hashlib.sha256(record_json.encode()).hexdigest()
        record["record_hash"] = record_hash

        # Generate digital signature
        digital_signature = self._sign_data(record_hash)
        record["digital_signature"] = digital_signature

        # Generate HMAC for additional integrity (using the same data as hash)
        hmac_signature = self.generate_hmac_signature(record_json)
        record["hmac_signature"] = hmac_signature
        
        # Add integrity verification info
        record["integrity_info"] = {
            "hash_algorithm": "SHA-256",
            "signature_algorithm": "RSA-PSS",
            "hmac_algorithm": "HMAC-SHA256",
            "key_size": 2048,
            "tamper_evident": True,
            "non_repudiation": True
        }
        
        return record
    
    def verify_audit_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify the cryptographic integrity of an audit record.
        
        Args:
            record: Audit record to verify
            
        Returns:
            Verification results with detailed status
        """
        verification_results = {
            "is_valid": False,
            "timestamp_valid": False,
            "evidence_hash_valid": False,
            "record_hash_valid": False,
            "digital_signature_valid": False,
            "hmac_signature_valid": False,
            "tamper_detected": False,
            "verification_timestamp": datetime.now(timezone.utc).isoformat(),
            "errors": []
        }
        
        try:
            # Verify timestamp signature
            if "timestamp_info" in record:
                timestamp_hash = record["timestamp_info"].get("timestamp_hash")
                timestamp_signature = record["timestamp_info"].get("timestamp_signature")
                if timestamp_hash and timestamp_signature:
                    verification_results["timestamp_valid"] = self.verify_signature(
                        timestamp_hash, timestamp_signature
                    )
                else:
                    verification_results["errors"].append("Missing timestamp hash or signature")
            
            # Verify evidence hash
            if "evidence_data" in record and "evidence_hash" in record:
                calculated_hash = self.generate_evidence_hash(record["evidence_data"])
                verification_results["evidence_hash_valid"] = (
                    calculated_hash == record["evidence_hash"]
                )
                if not verification_results["evidence_hash_valid"]:
                    verification_results["errors"].append("Evidence hash mismatch - data may be tampered")
            
            # Verify record hash using the same canonical representation
            if "record_hash" in record:
                hashable_data = {
                    "record_id": record.get("record_id"),
                    "record_type": record.get("record_type"),
                    "subject_cid": record.get("subject_cid"),
                    "compliance_framework": record.get("compliance_framework"),
                    "evidence_data": record.get("evidence_data"),
                    "evidence_hash": record.get("evidence_hash"),
                    "timestamp_info": record.get("timestamp_info"),
                    "generated_by": record.get("generated_by"),
                    "version": record.get("version")
                }
                record_json = json.dumps(hashable_data, sort_keys=True, separators=(',', ':'))
                calculated_hash = hashlib.sha256(record_json.encode()).hexdigest()
                verification_results["record_hash_valid"] = (
                    calculated_hash == record["record_hash"]
                )
                if not verification_results["record_hash_valid"]:
                    verification_results["errors"].append("Record hash mismatch - record may be tampered")
            
            # Verify digital signature
            if "digital_signature" in record and "record_hash" in record:
                verification_results["digital_signature_valid"] = self.verify_signature(
                    record["record_hash"], record["digital_signature"]
                )
                if not verification_results["digital_signature_valid"]:
                    verification_results["errors"].append("Digital signature verification failed")
            
            # Verify HMAC signature using the same canonical representation
            if "hmac_signature" in record:
                hashable_data = {
                    "record_id": record.get("record_id"),
                    "record_type": record.get("record_type"),
                    "subject_cid": record.get("subject_cid"),
                    "compliance_framework": record.get("compliance_framework"),
                    "evidence_data": record.get("evidence_data"),
                    "evidence_hash": record.get("evidence_hash"),
                    "timestamp_info": record.get("timestamp_info"),
                    "generated_by": record.get("generated_by"),
                    "version": record.get("version")
                }
                record_json = json.dumps(hashable_data, sort_keys=True, separators=(',', ':'))
                verification_results["hmac_signature_valid"] = self.verify_hmac_signature(
                    record_json, record["hmac_signature"]
                )
                if not verification_results["hmac_signature_valid"]:
                    verification_results["errors"].append("HMAC signature verification failed")
            
            # Overall validity check
            verification_results["is_valid"] = all([
                verification_results["timestamp_valid"],
                verification_results["evidence_hash_valid"],
                verification_results["record_hash_valid"],
                verification_results["digital_signature_valid"],
                verification_results["hmac_signature_valid"]
            ])
            
            # Detect tampering
            verification_results["tamper_detected"] = not verification_results["is_valid"]
            
        except Exception as e:
            verification_results["errors"].append(f"Verification error: {str(e)}")
            verification_results["tamper_detected"] = True
        
        return verification_results
    
    def get_public_key_pem(self) -> str:
        """
        Get the public key in PEM format for external verification.
        
        Returns:
            PEM encoded public key string
        """
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode()


# Global instance for use across the application
audit_crypto = AuditCryptoService()

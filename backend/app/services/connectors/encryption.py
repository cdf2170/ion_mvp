"""
Secure credential encryption/decryption for API connections.
Uses environment-based encryption keys with proper key rotation support.
"""

import os
import json
import base64
import logging
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class CredentialEncryption:
    """Handles secure encryption/decryption of API credentials."""
    
    def __init__(self):
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key from environment."""
        # Try to get key from environment
        env_key = os.getenv('CREDENTIAL_ENCRYPTION_KEY')
        if env_key:
            try:
                return base64.urlsafe_b64decode(env_key.encode())
            except Exception as e:
                logger.warning(f"Invalid encryption key in environment: {e}")
        
        # Generate key from master password + salt
        master_password = os.getenv('MASTER_ENCRYPTION_PASSWORD', 'default-dev-password-change-in-prod')
        salt = os.getenv('ENCRYPTION_SALT', 'default-salt-change-in-prod').encode()
        
        # Use PBKDF2 to derive key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        
        logger.info("Generated encryption key from master password")
        return key
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials dictionary to base64 string."""
        try:
            # Convert to JSON string
            json_str = json.dumps(credentials)
            
            # Encrypt
            encrypted_bytes = self.fernet.encrypt(json_str.encode())
            
            # Return as base64 string for database storage
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
            
        except Exception as e:
            logger.error(f"Failed to encrypt credentials: {e}")
            raise ValueError(f"Credential encryption failed: {str(e)}")
    
    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt base64 string back to credentials dictionary."""
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_credentials.encode())
            
            # Decrypt
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            
            # Parse JSON
            credentials = json.loads(decrypted_bytes.decode())
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise ValueError(f"Credential decryption failed: {str(e)}")


# Global instance
_credential_encryption = None

def get_credential_encryption() -> CredentialEncryption:
    """Get global credential encryption instance."""
    global _credential_encryption
    if _credential_encryption is None:
        _credential_encryption = CredentialEncryption()
    return _credential_encryption


def encrypt_credentials(credentials: Dict[str, Any]) -> str:
    """Convenience function to encrypt credentials."""
    return get_credential_encryption().encrypt_credentials(credentials)


def decrypt_credentials(encrypted_credentials: str) -> Dict[str, Any]:
    """Convenience function to decrypt credentials."""
    return get_credential_encryption().decrypt_credentials(encrypted_credentials)


def generate_encryption_key() -> str:
    """Generate a new encryption key for production use."""
    key = Fernet.generate_key()
    return base64.urlsafe_b64encode(key).decode()


# Production key rotation support
def rotate_credentials(old_encrypted: str, new_encryption_key: str) -> str:
    """Rotate credentials to new encryption key."""
    try:
        # Decrypt with old key
        old_encryption = _credential_encryption
        credentials = old_encryption.decrypt_credentials(old_encrypted)
        
        # Create new encryption instance with new key
        temp_key = base64.urlsafe_b64decode(new_encryption_key.encode())
        new_fernet = Fernet(temp_key)
        
        # Encrypt with new key
        json_str = json.dumps(credentials)
        encrypted_bytes = new_fernet.encrypt(json_str.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
        
    except Exception as e:
        logger.error(f"Failed to rotate credentials: {e}")
        raise ValueError(f"Credential rotation failed: {str(e)}")


if __name__ == "__main__":
    # CLI tool for generating keys and testing encryption
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "generate-key":
        print("Generated encryption key:")
        print(generate_encryption_key())
        print("\nSet this as CREDENTIAL_ENCRYPTION_KEY environment variable in production")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test encryption/decryption
        test_creds = {
            "tenant_id": "12345678-1234-1234-1234-123456789012",
            "client_id": "87654321-4321-4321-4321-210987654321",
            "client_secret": "super-secret-value-here"
        }
        
        print("Testing encryption/decryption...")
        encrypted = encrypt_credentials(test_creds)
        print(f"Encrypted: {encrypted[:50]}...")
        
        decrypted = decrypt_credentials(encrypted)
        print(f"Decrypted: {decrypted}")
        
        print(" Encryption test passed!" if decrypted == test_creds else " Encryption test failed!")
    
    else:
        print("Usage:")
        print("  python encryption.py generate-key  # Generate new encryption key")
        print("  python encryption.py test          # Test encryption/decryption")

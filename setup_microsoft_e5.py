#!/usr/bin/env python3
"""
Microsoft E5 Tenant Setup Script
Secure command-line tool for setting up Microsoft Graph integration.
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from backend.app.services.connectors.encryption import generate_encryption_key, encrypt_credentials


def setup_microsoft_e5():
    """Interactive setup for Microsoft E5 tenant integration."""
    
    print(" Microsoft E5 Tenant Secure Setup")
    print("=" * 50)
    
    # Step 1: Collect credentials
    print("\n Step 1: Azure AD App Registration Details")
    print("(Get these from Azure Portal > Azure AD > App registrations)")
    
    tenant_id = input("Enter your Tenant ID (GUID): ").strip()
    client_id = input("Enter your Client ID (Application ID): ").strip()
    client_secret = input("Enter your Client Secret: ").strip()
    
    if not all([tenant_id, client_id, client_secret]):
        print(" All fields are required!")
        return False
    
    # Step 2: Generate encryption key if needed
    print("\n🔑 Step 2: Encryption Key")
    use_existing_key = input("Do you have an existing encryption key? (y/n): ").lower().startswith('y')
    
    if use_existing_key:
        encryption_key = input("Enter your encryption key: ").strip()
    else:
        encryption_key = generate_encryption_key()
        print(f"Generated new encryption key: {encryption_key}")
        print("⚠  SAVE THIS KEY - you'll need it for production!")
    
    # Step 3: Test connection
    print("\n🧪 Step 3: Testing Connection")
    
    credentials = {
        "tenant_id": tenant_id,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    # Test OAuth2 token acquisition
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    try:
        print("  Testing OAuth2 token acquisition...")
        response = requests.post(token_url, data=token_data, timeout=30)
        response.raise_for_status()
        
        token_info = response.json()
        access_token = token_info['access_token']
        
        print("   OAuth2 token acquired successfully")
        
        # Test Graph API call
        print("  Testing Microsoft Graph API call...")
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        graph_response = requests.get(
            "https://graph.microsoft.com/v1.0/organization",
            headers=headers,
            timeout=30
        )
        graph_response.raise_for_status()
        
        org_data = graph_response.json()
        org_info = org_data.get('value', [{}])[0]
        org_name = org_info.get('displayName', 'Unknown Organization')
        
        print(f"   Connected to: {org_name}")
        
    except requests.exceptions.RequestException as e:
        print(f"   Connection test failed: {e}")
        print("\nPlease check:")
        print("  - Tenant ID is correct")
        print("  - Client ID is correct") 
        print("  - Client secret is valid and not expired")
        print("  - App has required permissions with admin consent")
        return False
    
    # Step 4: Create environment files
    print("\n Step 4: Creating Environment Files")
    
    # Create .env for local development
    env_content = f"""# Microsoft E5 Tenant (Development)
MICROSOFT_TENANT_ID={tenant_id}
MICROSOFT_CLIENT_ID={client_id}
MICROSOFT_CLIENT_SECRET={client_secret}

# Encryption (Development)
CREDENTIAL_ENCRYPTION_KEY={encryption_key}
MASTER_ENCRYPTION_PASSWORD=dev-password-change-in-prod
ENCRYPTION_SALT=dev-salt-change-in-prod

# Database (Development)
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5435/mvp_db
DEMO_API_TOKEN=token 21700
DEBUG=true
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("   Created .env file for local development")
    
    # Create Railway deployment commands
    railway_commands = f"""#!/bin/bash
# Railway Production Environment Variables
# Run these commands to set up production secrets

echo "Setting up Microsoft E5 tenant in Railway..."

railway variables set CREDENTIAL_ENCRYPTION_KEY="{encryption_key}"
railway variables set MICROSOFT_TENANT_ID="{tenant_id}"
railway variables set MICROSOFT_CLIENT_ID="{client_id}"
railway variables set MICROSOFT_CLIENT_SECRET="{client_secret}"

# Optional: Set custom encryption password (more secure)
# railway variables set MASTER_ENCRYPTION_PASSWORD="your-super-secure-master-password"
# railway variables set ENCRYPTION_SALT="your-unique-salt-value"

echo " Railway environment variables configured!"
echo "Now run: railway up"
"""
    
    with open('setup_railway_microsoft.sh', 'w') as f:
        f.write(railway_commands)
    
    os.chmod('setup_railway_microsoft.sh', 0o755)
    print("   Created setup_railway_microsoft.sh for production deployment")
    
    # Step 5: Update .gitignore
    gitignore_entries = ['.env', '*.env', '.env.*']
    
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            existing = f.read()
        
        new_entries = []
        for entry in gitignore_entries:
            if entry not in existing:
                new_entries.append(entry)
        
        if new_entries:
            with open('.gitignore', 'a') as f:
                f.write('\n# Environment files\n')
                for entry in new_entries:
                    f.write(f'{entry}\n')
            print("   Updated .gitignore to exclude environment files")
    
    # Step 6: Success summary
    print("\n Setup Complete!")
    print("=" * 50)
    print(f"Organization: {org_name}")
    print(f"Tenant ID: {tenant_id}")
    print(f"Client ID: {client_id}")
    print("\n Next Steps:")
    print("1. Start local server: python -m uvicorn backend.app.main:app --reload")
    print("2. Test connection: curl -H 'Authorization: Bearer token 21700' http://localhost:8000/v1/microsoft/status")
    print("3. Deploy to Railway: ./setup_railway_microsoft.sh && railway up")
    print("\n🔒 Security Notes:")
    print("- Credentials are encrypted before database storage")
    print("- .env file is excluded from git")
    print("- Production secrets are in Railway environment variables only")
    
    return True


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Microsoft E5 Tenant Setup Script")
        print("Usage: python setup_microsoft_e5.py")
        print("\nThis script will:")
        print("- Collect your Azure AD app registration details")
        print("- Test the connection to Microsoft Graph")
        print("- Generate encryption keys for secure credential storage")
        print("- Create environment files for local development")
        print("- Generate Railway deployment scripts")
        return
    
    try:
        success = setup_microsoft_e5()
        if success:
            print("\n Microsoft E5 tenant setup completed successfully!")
        else:
            print("\n Setup failed. Please check the errors above and try again.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠  Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

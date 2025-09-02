#!/usr/bin/env python3
"""
Railway.app deployment setup script
Initializes the system with teams and API keys for Railway deployment
"""

import os
import sys
import sqlite3
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_database_exists() -> bool:
    """Check if the database already exists and has teams"""
    db_path = os.getenv("DATABASE_PATH", "api_keys.db")
    
    if not os.path.exists(db_path):
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM teams")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except:
        return False

def get_admin_key() -> Optional[str]:
    """Get existing admin API key if available"""
    db_path = os.getenv("DATABASE_PATH", "api_keys.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ak.hashed_key FROM api_keys ak
            JOIN teams t ON ak.team_id = t.team_id
            WHERE t.tier = 'internal'
            LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Note: This returns the hash, not the actual key
            # In production, you'd store the key securely or regenerate
            return "existing-admin-key-found"
        return None
    except:
        return None

def setup_for_railway():
    """Setup teams and API keys for Railway deployment"""
    print("🚂 Setting up Vectorized CPT for Railway deployment...")
    
    # Check if already setup
    if check_database_exists():
        print("✅ Database already exists with teams!")
        existing_key = get_admin_key()
        if existing_key:
            print("🔑 Admin key already configured")
            return existing_key
    
    try:
        # Import after path setup
        from setup_teams import create_internal_team, create_sample_teams
        
        print("🔧 Creating admin team...")
        admin_team_id, admin_api_key = create_internal_team()
        
        print("👥 Creating sample teams...")
        teams = create_sample_teams()
        
        # Save API key to environment file for Railway
        env_file = "/app/.env"
        with open(env_file, "w") as f:
            f.write(f"VECTORIZED_CPT_API_KEY={admin_api_key}\n")
        
        print(f"\n✅ Setup complete! Admin API key: {admin_api_key}")
        print(f"💾 API key saved to {env_file}")
        
        return admin_api_key
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def validate_setup():
    """Validate that the setup worked correctly"""
    try:
        from api_gateway.auth import api_key_manager
        
        teams = api_key_manager.list_all_teams()
        print(f"\n🔍 Found {len(teams)} teams:")
        for team in teams:
            print(f"   - {team.team_name} ({team.tier})")
        
        return True
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

if __name__ == "__main__":
    # Run setup
    api_key = setup_for_railway()
    
    if api_key:
        # Validate
        if validate_setup():
            print("\n🎉 Railway setup completed successfully!")
            print(f"🔑 Use this API key: {api_key}")
            print("🚂 Deploy to Railway with: railway up")
        else:
            print("\n⚠️  Setup completed but validation failed")
            sys.exit(1)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)
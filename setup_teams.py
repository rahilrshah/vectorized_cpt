#!/usr/bin/env python3
"""
Team Setup and Management Script
Helps initialize teams and API keys for the Vectorized CPT system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_gateway.auth import api_key_manager
from api_gateway.models import TeamTier


def create_internal_team():
    """Create the internal admin team"""
    print("🔧 Creating internal admin team...")
    
    team_id = api_key_manager.create_team(
        team_name="Internal Admin Team",
        tier=TeamTier.internal,
        contact_email="admin@vectorized-cpt.com",
        enabled_features=["debug_endpoints", "advanced_analytics", "bulk_processing"],
        max_results_limit=100,
        rate_limit_multiplier=5.0
    )
    
    # Create admin API key
    api_key, key_id = api_key_manager.generate_api_key(
        team_id=team_id,
        user_id="admin",
        rate_limit_per_hour=5000
    )
    
    print(f"✅ Internal admin team created!")
    print(f"   Team ID: {team_id}")
    print(f"   Admin API Key: {api_key}")
    print(f"   Key ID: {key_id}")
    print(f"   Rate Limit: 5000/hour")
    print()
    
    return team_id, api_key


def create_sample_teams():
    """Create sample teams for different access levels"""
    teams = []
    
    # Basic team
    print("👥 Creating basic team...")
    basic_team_id = api_key_manager.create_team(
        team_name="Basic Development Team",
        tier=TeamTier.basic,
        contact_email="basic@example.com",
        enabled_features=["medical_extract", "cpt_search"],
        max_results_limit=20,
        rate_limit_multiplier=1.0
    )
    
    basic_api_key, basic_key_id = api_key_manager.generate_api_key(
        team_id=basic_team_id,
        user_id="basic_user",
        rate_limit_per_hour=100
    )
    
    teams.append({
        "name": "Basic Development Team",
        "tier": "basic",
        "team_id": basic_team_id,
        "api_key": basic_api_key,
        "features": ["medical_extract", "cpt_search"],
        "rate_limit": 100
    })
    
    # Premium team
    print("🚀 Creating premium team...")
    premium_team_id = api_key_manager.create_team(
        team_name="Premium Healthcare Team",
        tier=TeamTier.premium,
        contact_email="premium@example.com",
        enabled_features=["comprehensive_coding", "pdf_processing"],
        max_results_limit=50,
        rate_limit_multiplier=2.0
    )
    
    premium_api_key, premium_key_id = api_key_manager.generate_api_key(
        team_id=premium_team_id,
        user_id="premium_user",
        rate_limit_per_hour=1000
    )
    
    teams.append({
        "name": "Premium Healthcare Team", 
        "tier": "premium",
        "team_id": premium_team_id,
        "api_key": premium_api_key,
        "features": ["comprehensive_coding", "pdf_processing"],
        "rate_limit": 2000  # 1000 * 2.0 multiplier
    })
    
    # Enterprise team
    print("🏢 Creating enterprise team...")
    enterprise_team_id = api_key_manager.create_team(
        team_name="Enterprise Medical System",
        tier=TeamTier.enterprise,
        contact_email="enterprise@example.com",
        enabled_features=["bulk_processing", "advanced_analytics", "priority_support"],
        max_results_limit=100,
        rate_limit_multiplier=3.0
    )
    
    enterprise_api_key, enterprise_key_id = api_key_manager.generate_api_key(
        team_id=enterprise_team_id,
        user_id="enterprise_user",
        rate_limit_per_hour=2000
    )
    
    teams.append({
        "name": "Enterprise Medical System",
        "tier": "enterprise", 
        "team_id": enterprise_team_id,
        "api_key": enterprise_api_key,
        "features": ["bulk_processing", "advanced_analytics", "priority_support"],
        "rate_limit": 6000  # 2000 * 3.0 multiplier
    })
    
    print("✅ Sample teams created!")
    return teams


def display_team_summary(teams, admin_key):
    """Display a summary of all created teams"""
    print("\n" + "="*80)
    print("🎉 VECTORIZED CPT API GATEWAY - TEAM SETUP COMPLETE")
    print("="*80)
    print()
    print("🔑 ADMIN ACCESS:")
    print(f"   API Key: {admin_key}")
    print(f"   Usage: Use this key for team management and admin functions")
    print()
    print("👥 CREATED TEAMS:")
    print()
    
    for i, team in enumerate(teams, 1):
        print(f"{i}. {team['name']} ({team['tier'].upper()})")
        print(f"   Team ID: {team['team_id']}")
        print(f"   API Key: {team['api_key']}")
        print(f"   Rate Limit: {team['rate_limit']}/hour")
        print(f"   Features: {', '.join(team['features'])}")
        print()
    
    print("📋 NEXT STEPS:")
    print("1. Start the API Gateway: python -m uvicorn api_gateway.main:app --reload --port 8000")
    print("2. Test with: curl -H 'Authorization: Bearer <api_key>' http://localhost:8000/health")
    print("3. View docs at: http://localhost:8000/docs")
    print("4. Team management: http://localhost:8000/api/v1/admin/teams")
    print()
    print("🔒 SECURITY NOTES:")
    print("- API keys are shown only once - save them securely!")
    print("- Internal tier required for team management endpoints")
    print("- Feature access is automatically controlled by team tier")
    print("- Rate limits are applied per API key per hour")
    print()


def test_team_features():
    """Test that feature flags are working correctly"""
    print("🧪 Testing feature flag system...")
    
    # Get all teams and test feature access
    teams = api_key_manager.list_all_teams()
    
    for team in teams:
        print(f"   Testing team: {team.team_name} ({team.tier})")
        available_features = api_key_manager.get_available_features(team)
        feature_names = [f.flag_name for f in available_features]
        print(f"   Available features: {feature_names}")
    
    print("✅ Feature flag testing complete!")


def main():
    """Main setup function"""
    print("🏥 Vectorized CPT API Gateway - Team Setup")
    print("=" * 50)
    print()
    
    try:
        # Create internal admin team first
        admin_team_id, admin_api_key = create_internal_team()
        
        # Create sample teams
        teams = create_sample_teams()
        
        # Test feature flags
        test_team_features()
        
        # Display summary
        display_team_summary(teams, admin_api_key)
        
        print("🎯 Setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
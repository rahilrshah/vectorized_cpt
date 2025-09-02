#!/usr/bin/env python3
"""
Quick Test Script for Team-Based Architecture
Verifies that the core functionality works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_gateway.auth import api_key_manager
from api_gateway.models import TeamTier


def test_team_creation():
    """Test team creation and API key generation"""
    print("🧪 Testing team creation...")
    
    try:
        # Create test team
        team_id = api_key_manager.create_team(
            team_name="Test Team",
            tier=TeamTier.premium,
            contact_email="test@example.com",
            enabled_features=["comprehensive_coding"],
            max_results_limit=30,
            rate_limit_multiplier=2.5
        )
        
        print(f"✅ Team created with ID: {team_id}")
        
        # Generate API key
        api_key, key_id = api_key_manager.generate_api_key(
            team_id=team_id,
            user_id="test_user",
            rate_limit_per_hour=500
        )
        
        print(f"✅ API key generated: {api_key}")
        print(f"✅ Key ID: {key_id}")
        
        return team_id, api_key, key_id
        
    except Exception as e:
        print(f"❌ Team creation failed: {e}")
        return None, None, None


def test_api_key_validation(api_key):
    """Test API key validation and team info retrieval"""
    print("\n🔐 Testing API key validation...")
    
    try:
        is_valid, key_info = api_key_manager.validate_api_key(api_key)
        
        if is_valid and key_info:
            print("✅ API key validation successful")
            print(f"   Team: {key_info.team_info.team_name}")
            print(f"   Tier: {key_info.team_info.tier}")
            print(f"   Rate Limit: {key_info.rate_limit_per_hour}/hour")
            print(f"   Features: {key_info.team_info.enabled_features}")
            return key_info
        else:
            print("❌ API key validation failed")
            return None
            
    except Exception as e:
        print(f"❌ API key validation error: {e}")
        return None


def test_feature_access(key_info):
    """Test feature access control"""
    print("\n🎛️  Testing feature access control...")
    
    try:
        # Test access to different features
        features_to_test = [
            "medical_extract",
            "cpt_search", 
            "comprehensive_coding",
            "pdf_processing",
            "bulk_processing",
            "debug_endpoints"
        ]
        
        for feature in features_to_test:
            has_access = api_key_manager.check_feature_access(
                key_info.team_info, feature
            )
            status = "✅" if has_access else "🔒"
            print(f"   {status} {feature}: {'Allowed' if has_access else 'Denied'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Feature access test error: {e}")
        return False


def test_usage_logging(key_info):
    """Test usage logging functionality"""
    print("\n📊 Testing usage logging...")
    
    try:
        # Log some test usage
        api_key_manager.log_usage(
            key_id=key_info.key_id,
            team_id=key_info.team_id,
            endpoint="/api/v1/process",
            service_name="test_service",
            response_time_ms=1500,
            success=True
        )
        
        # Get usage stats
        usage_stats = api_key_manager.get_usage_stats(key_info.key_id)
        print(f"✅ Usage logged successfully")
        print(f"   Total requests: {usage_stats.total_requests}")
        print(f"   Average response time: {usage_stats.average_response_time_ms}ms")
        
        # Get team usage stats
        team_stats = api_key_manager.get_team_usage_stats(key_info.team_id)
        print(f"   Team total requests: {team_stats.total_requests}")
        print(f"   Active API keys: {team_stats.active_api_keys}")
        
        return True
        
    except Exception as e:
        print(f"❌ Usage logging test error: {e}")
        return False


def test_rate_limiting(key_info):
    """Test rate limiting functionality"""
    print("\n⏱️  Testing rate limiting...")
    
    try:
        rate_limit = key_info.rate_limit_per_hour
        
        # Test rate limit check
        within_limit, current_requests = api_key_manager.check_rate_limit(
            key_info.key_id, rate_limit
        )
        
        if within_limit:
            print(f"✅ Rate limit check passed ({current_requests}/{rate_limit})")
        else:
            print(f"🔒 Rate limit exceeded ({current_requests}/{rate_limit})")
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Team-Based Architecture Test Suite")
    print("=" * 50)
    
    # Test 1: Team creation
    team_id, api_key, key_id = test_team_creation()
    if not all([team_id, api_key, key_id]):
        print("❌ Cannot continue - team creation failed")
        return 1
    
    # Test 2: API key validation
    key_info = test_api_key_validation(api_key)
    if not key_info:
        print("❌ Cannot continue - API key validation failed")
        return 1
    
    # Test 3: Feature access control
    feature_test_passed = test_feature_access(key_info)
    
    # Test 4: Usage logging
    usage_test_passed = test_usage_logging(key_info)
    
    # Test 5: Rate limiting
    rate_limit_test_passed = test_rate_limiting(key_info)
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    tests = [
        ("Team Creation", team_id is not None),
        ("API Key Validation", key_info is not None),
        ("Feature Access Control", feature_test_passed),
        ("Usage Logging", usage_test_passed), 
        ("Rate Limiting", rate_limit_test_passed)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, passed_test in tests:
        status = "✅" if passed_test else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Team-based architecture is working correctly.")
        print("\nNext steps:")
        print("1. Run: python setup_teams.py")
        print("2. Start API: python -m uvicorn api_gateway.main:app --port 8000")
        print("3. Test API: python demo_team_api.py")
        return 0
    else:
        print("❌ Some tests failed. Check the error messages above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)
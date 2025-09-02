#!/usr/bin/env python3
"""
Team-Based API Demo Script
Demonstrates the new team-based access control system
"""

import asyncio
import aiohttp
import json
import sys


class TeamAPIDemo:
    """Demonstrates team-based API access patterns"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def api_request(self, method, endpoint, api_key, data=None):
        """Make an API request with proper authentication"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                async with self.session.get(url, headers=headers) as response:
                    return response.status, await response.json()
            elif method == "POST":
                async with self.session.post(url, headers=headers, json=data) as response:
                    return response.status, await response.json()
        except Exception as e:
            return 500, {"error": str(e)}
    
    async def demo_health_check(self):
        """Demo: Health check (no auth required)"""
        print("🏥 Testing health check endpoint...")
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                health_data = await response.json()
                print(f"   Status: {health_data['gateway_status']}")
                print(f"   Services: {health_data['healthy_services']}/{health_data['total_services']} healthy")
                
                # Show architecture type
                services = health_data.get('services_status', {})
                if 'billing_monolith' in services:
                    print("   ✅ Running on monolithic architecture (optimal performance)")
                else:
                    print("   ⚠️  Running on microservices architecture")
                
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
    
    async def demo_team_access_levels(self, teams_data):
        """Demo: Different access levels for different teams"""
        print("\n🔐 Testing team-based access controls...")
        
        for team in teams_data:
            print(f"\n   Testing {team['name']} ({team['tier']})...")
            api_key = team['api_key']
            
            # Test basic medical extraction
            status, response = await self.api_request(
                "POST", "/api/v1/medical/extract",
                api_key,
                {"text": "Patient underwent knee arthroscopy"}
            )
            
            if status == 200:
                print(f"   ✅ Medical extraction: Success")
                extracted = response.get('data', {}).get('extracted_procedures', 'N/A')
                print(f"      Extracted: {extracted[:50]}...")
            else:
                print(f"   ❌ Medical extraction: Failed ({status})")
            
            # Test CPT search
            status, response = await self.api_request(
                "POST", "/api/v1/cpt/search",
                api_key,
                {"procedures": "knee arthroscopy", "max_results": 5}
            )
            
            if status == 200:
                results_count = response.get('data', {}).get('total_results', 0)
                print(f"   ✅ CPT search: Found {results_count} codes")
            else:
                print(f"   ❌ CPT search: Failed ({status})")
            
            # Test comprehensive coding (premium+ only)
            status, response = await self.api_request(
                "POST", "/api/v1/medical/code-complete",
                api_key,
                {
                    "primary_codes": [{"cpt_code": "29881", "description": "Knee arthroscopy"}],
                    "medical_text": "Patient underwent knee arthroscopy"
                }
            )
            
            if status == 200:
                print(f"   ✅ Comprehensive coding: Success")
            elif status == 403:
                print(f"   🔒 Comprehensive coding: Access denied (expected for {team['tier']})")
            else:
                print(f"   ❌ Comprehensive coding: Failed ({status})")
    
    async def demo_complete_workflow(self, api_key, tier_name):
        """Demo: Complete workflow with a single API call"""
        print(f"\n🔄 Testing complete workflow ({tier_name})...")
        
        medical_note = """
        Patient: John Smith
        Date: 2024-01-15
        
        PROCEDURE: Arthroscopic partial meniscectomy, right knee
        
        INDICATION: The patient is a 45-year-old male with a torn medial meniscus 
        of the right knee confirmed by MRI. Conservative treatment failed.
        
        PROCEDURE DETAILS: Under general anesthesia, diagnostic arthroscopy was 
        performed followed by partial meniscectomy of the torn medial meniscus. 
        The joint was irrigated and instruments removed. Patient tolerated 
        procedure well.
        
        POST-OP: Patient discharged home with crutches and follow-up in 2 weeks.
        """
        
        status, response = await self.api_request(
            "POST", "/api/v1/process",
            api_key,
            {
                "text": medical_note,
                "max_results": 10,
                "include_comprehensive": True
            }
        )
        
        if status == 200:
            print("   ✅ Complete workflow: Success")
            print(f"   📝 Extracted procedures: {response.get('step2_extracted_procedures', 'N/A')[:80]}...")
            
            cpt_results = response.get('step3_cpt_results', [])
            print(f"   🔍 Found {len(cpt_results)} CPT codes")
            
            if cpt_results:
                top_code = cpt_results[0]
                print(f"   🥇 Top match: {top_code.get('cpt_code')} ({top_code.get('similarity', 0):.2f} similarity)")
            
            comprehensive = response.get('step4_comprehensive_codes')
            if comprehensive:
                print("   🎯 Comprehensive coding: Available")
            else:
                print("   🔒 Comprehensive coding: Not available for this tier")
            
            # Show team limits applied
            team_limits = response.get('team_limits_applied', {})
            print(f"   ⚖️  Team limits: Max results = {team_limits.get('max_results', 'N/A')}")
            
        else:
            print(f"   ❌ Complete workflow: Failed ({status})")
            error_detail = response.get('detail', 'Unknown error')
            print(f"      Error: {error_detail}")
    
    async def demo_usage_analytics(self, teams_data):
        """Demo: Usage analytics and team monitoring"""
        print("\n📊 Testing usage analytics...")
        
        for team in teams_data:
            api_key = team['api_key']
            team_id = team['team_id']
            
            # Get individual usage stats
            status, response = await self.api_request(
                "GET", "/api/v1/usage",
                api_key
            )
            
            if status == 200:
                stats = response
                print(f"   {team['name']}: {stats['total_requests']} total requests")
            
            # Get team-wide usage stats
            status, response = await self.api_request(
                "GET", f"/api/v1/teams/{team_id}/usage",
                api_key
            )
            
            if status == 200:
                team_stats = response
                print(f"   Team stats: {team_stats['total_requests']} requests, {team_stats['active_api_keys']} active keys")
    
    async def demo_feature_discovery(self, teams_data):
        """Demo: Feature discovery for different teams"""
        print("\n🎛️  Testing feature discovery...")
        
        for team in teams_data:
            api_key = team['api_key']
            team_id = team['team_id']
            
            status, response = await self.api_request(
                "GET", f"/api/v1/teams/{team_id}/features",
                api_key
            )
            
            if status == 200:
                features = response
                feature_names = [f['flag_name'] for f in features]
                print(f"   {team['name']}: {', '.join(feature_names)}")
            else:
                print(f"   {team['name']}: Failed to get features ({status})")


async def main():
    """Main demo function"""
    print("🚀 Vectorized CPT API - Team-Based Access Demo")
    print("=" * 60)
    
    # Sample team data (would normally come from setup script output)
    teams_data = [
        {
            "name": "Basic Development Team",
            "tier": "basic",
            "team_id": "basic-team-id",
            "api_key": "vcp_your_basic_api_key_here",
            "features": ["medical_extract", "cpt_search"]
        },
        {
            "name": "Premium Healthcare Team",
            "tier": "premium", 
            "team_id": "premium-team-id",
            "api_key": "vcp_your_premium_api_key_here",
            "features": ["comprehensive_coding", "pdf_processing"]
        }
    ]
    
    print("\n⚠️  NOTE: This demo requires:")
    print("1. API Gateway running on localhost:8000")
    print("2. Valid API keys (run setup_teams.py first)")
    print("3. Replace the sample API keys above with real ones")
    print()
    
    # Ask user if they want to continue with demo API keys
    response = input("Continue with demo? (y/N): ")
    if response.lower() != 'y':
        print("Demo cancelled. Run setup_teams.py first to get real API keys.")
        return
    
    async with TeamAPIDemo() as demo:
        # Test system health
        await demo.demo_health_check()
        
        # Test team access levels
        await demo.demo_team_access_levels(teams_data)
        
        # Test complete workflows
        for team in teams_data:
            await demo.demo_complete_workflow(team['api_key'], team['name'])
        
        # Test analytics
        await demo.demo_usage_analytics(teams_data)
        
        # Test feature discovery
        await demo.demo_feature_discovery(teams_data)
    
    print("\n🎉 Demo completed!")
    print("\nNext steps:")
    print("- Run setup_teams.py to create real teams and API keys")
    print("- Test the API Gateway with your applications")
    print("- Monitor usage via /api/v1/teams/{team_id}/usage")
    print("- Manage teams via /api/v1/admin/* endpoints")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)
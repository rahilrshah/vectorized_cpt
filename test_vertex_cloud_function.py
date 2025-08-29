#!/usr/bin/env python3
"""
Test the new Vertex AI Cloud Function
"""

import requests
import json
import time

def test_vertex_cloud_function():
    """Test the new findSimilarCptCodesVertex Cloud Function"""
    print("=" * 80)
    print("🧪 TESTING VERTEX AI CLOUD FUNCTION")
    print("=" * 80)
    
    # Use the new Vertex AI function endpoint
    function_url = "https://us-central1-cpt-code-vectorized-dataset.cloudfunctions.net/findSimilarCptCodesVertex"
    
    # Test cases
    test_cases = [
        {
            "name": "Knee Surgery",
            "text": "Bilateral total knee arthroplasty with patellar resurfacing"
        },
        {
            "name": "Simple Procedure",
            "text": "Removal of skin lesion on arm"
        },
        {
            "name": "Heart Surgery",
            "text": "Coronary artery bypass graft surgery"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 TEST {i}: {test_case['name']}")
        print(f"Query: {test_case['text']}")
        print("-" * 60)
        
        test_data = {"data": {"text": test_case["text"]}}
        
        try:
            start_time = time.time()
            response = requests.post(
                function_url,
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=180  # Allow more time for Vertex AI processing
            )
            end_time = time.time()
            
            print(f"⏱️  Response time: {end_time - start_time:.2f}s")
            print(f"📊 HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS!")
                
                if 'result' in result:
                    if 'results' in result['result'] and len(result['result']['results']) > 0:
                        matches = result['result']['results']
                        print(f"🎯 Found {len(matches)} matches")
                        
                        # Show top matches
                        for j, match in enumerate(matches[:3]):
                            cpt = match.get('cpt_code', match.get('CPT Codes', 'N/A'))
                            desc = match.get('description', match.get('Descriptions', 'N/A'))
                            similarity = match.get('similarity', 'N/A')
                            print(f"   {j+1}. CPT {cpt} (similarity: {similarity:.4f})")
                            print(f"      {desc[:80]}...")
                            
                    elif 'status' in result['result'] and result['result']['status'] == 'service_initializing':
                        print(f"⏳ SERVICE INITIALIZING")
                        print(f"   Message: {result['result'].get('message', 'Unknown')}")
                        print(f"   This is expected - the Vertex AI deployment is still in progress")
                        
                    elif 'status' in result['result'] and result['result']['status'] == 'no_results':
                        print(f"⚠️  NO RESULTS FOUND")
                        print(f"   Message: {result['result'].get('message', 'Unknown')}")
                        
                    else:
                        print(f"📦 Unexpected result format: {result}")
                        
            else:
                print(f"❌ HTTP Error {response.status_code}")
                error_text = response.text[:500]
                print(f"Error: {error_text}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️  Request timed out (this might indicate deployment is still in progress)")
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        # Small delay between tests
        if i < len(test_cases):
            print("⏸️  Waiting 3 seconds before next test...")
            time.sleep(3)
    
    print("\n" + "=" * 80)
    print("📊 VERTEX AI CLOUD FUNCTION TEST COMPLETE")
    print("=" * 80)

def check_deployment_status():
    """Check if the Vertex AI deployment is ready"""
    print("🔍 Checking Vertex AI deployment status...")
    
    try:
        # Simple status check using Python utility
        from vertex_vector_search import check_vertex_status
        
        status = check_vertex_status()
        
        print(f"📊 Status: {status['status']}")
        print(f"📋 Message: {status['message']}")
        
        if status['status'] == 'ready':
            print("🎉 Vertex AI Vector Search is ready for testing!")
            return True
        elif status['status'] == 'deploying':
            print("⏳ Deployment still in progress...")
            print("   Estimated time remaining: 10-30 minutes")
            return False
        else:
            print("❌ Deployment issue detected")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not check status: {e}")
        print("   This is normal if deployment is still in progress")
        return False

if __name__ == '__main__':
    print("🚀 Starting Vertex AI Cloud Function test...")
    
    # Check deployment status first
    is_ready = check_deployment_status()
    
    print(f"\n📋 Proceeding with Cloud Function test...")
    print(f"   Note: Even if not ready, we can test the function response")
    
    # Test the function regardless of status
    test_vertex_cloud_function()
    
    if not is_ready:
        print(f"\n💡 If tests show 'service_initializing', try again in 15-20 minutes")
        print(f"   The Vertex AI deployment typically takes 30-45 minutes total")
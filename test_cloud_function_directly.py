import requests
import json
import time
import datetime

def test_cloud_function_directly():
    """Test the Cloud Function directly to see if it's working"""
    print("="*80)
    print("🧪 TESTING CLOUD FUNCTION DIRECTLY")
    print("="*80)
    
    # Cloud Function URL - this should be accessible directly
    function_url = "https://us-central1-cpt-code-vectorized-dataset.cloudfunctions.net/findSimilarCptCodes"
    
    # Test data - simple knee surgery description
    test_data = {
        "data": {
            "text": "Bilateral total knee arthroplasty with patellar resurfacing; Right knee lateral release."
        }
    }
    
    print(f"Function URL: {function_url}")
    print(f"Test query: {test_data['data']['text']}")
    print(f"Testing at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*60)
    
    try:
        print("🚀 Sending request to Cloud Function...")
        
        start_time = time.time()
        
        response = requests.post(
            function_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=120  # 2 minute timeout
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"📊 Response received in {response_time:.2f} seconds")
        print(f"📋 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ SUCCESS! Cloud Function returned data")
                print(f"📦 Response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                
                if 'result' in result and 'results' in result['result']:
                    results = result['result']['results']
                    print(f"🎯 Found {len(results)} CPT code matches!")
                    
                    print(f"\n🏆 TOP RESULTS:")
                    for i, match in enumerate(results[:5]):
                        cpt_code = match.get('cpt_code', match.get('CPT Codes', 'N/A'))
                        description = match.get('description', match.get('Descriptions', 'N/A'))
                        print(f"  {i+1}. CPT {cpt_code}")
                        print(f"     {description[:80]}...")
                    
                    # Check if we found knee-related codes
                    knee_keywords = ['knee', 'arthroplasty', 'patella', 'meniscus', 'cruciate', 'femoral', 'tibial']
                    knee_matches = 0
                    
                    for match in results[:10]:
                        desc = str(match.get('description', match.get('Descriptions', ''))).lower()
                        if any(keyword in desc for keyword in knee_keywords):
                            knee_matches += 1
                    
                    print(f"\n📊 Analysis:")
                    print(f"   Knee-related matches in top 10: {knee_matches}/10")
                    
                    if knee_matches >= 5:
                        print(f"   ✅ EXCELLENT! High relevance to knee surgery")
                    elif knee_matches >= 2:
                        print(f"   ⚠️  MODERATE relevance to knee surgery")
                    else:
                        print(f"   ❌ LOW relevance - possible search issue")
                        
                elif 'result' in result:
                    print(f"📦 Raw result: {result['result']}")
                else:
                    print(f"📦 Full response: {result}")
                    
                return True, "SUCCESS"
                
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response")
                print(f"📄 Raw response: {response.text[:500]}")
                return False, "Invalid JSON"
                
        else:
            print(f"❌ HTTP Error {response.status_code}")
            try:
                error_data = response.json()
                print(f"📄 Error details: {error_data}")
                
                error_msg = str(error_data)
                if 'index is currently building' in error_msg.lower():
                    print(f"🔧 DIAGNOSIS: Vector index still building")
                    return False, "Index building"
                elif 'failed_precondition' in error_msg.lower():
                    print(f"🔧 DIAGNOSIS: Vector index not ready (FAILED_PRECONDITION)")
                    return False, "Index not ready"
                else:
                    print(f"🔧 DIAGNOSIS: Other error")
                    return False, f"HTTP {response.status_code}"
                    
            except json.JSONDecodeError:
                print(f"📄 Raw error response: {response.text}")
                return False, f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        print(f"⏰ Request timed out after 120 seconds")
        return False, "Timeout"
        
    except requests.exceptions.ConnectionError:
        print(f"🔌 Connection error - check internet connection")
        return False, "Connection error"
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, f"Error: {e}"

def continuous_function_testing():
    """Continuously test the Cloud Function until it works"""
    print("🔄 CONTINUOUS CLOUD FUNCTION TESTING")
    print("="*60)
    print("Testing every 2 minutes until the index is ready...")
    print("Press Ctrl+C to stop")
    print()
    
    test_count = 0
    start_time = datetime.datetime.now()
    
    while True:
        test_count += 1
        current_time = datetime.datetime.now()
        elapsed = current_time - start_time
        
        print(f"🧪 TEST #{test_count} - {current_time.strftime('%H:%M:%S')} (elapsed: {elapsed})")
        
        success, status = test_cloud_function_directly()
        
        if success:
            print(f"\n🎉 CLOUD FUNCTION IS WORKING!")
            print(f"🌐 Website should now be fully functional!")
            print(f"🔗 Try: https://cpt-code-vectorized-dataset.web.app")
            break
        else:
            print(f"⏳ Status: {status}")
            if "index" in status.lower():
                print(f"💡 Index is still building, this is expected")
            
        print(f"⏸️  Waiting 2 minutes before next test...")
        print("-" * 40)
        
        try:
            time.sleep(120)  # Wait 2 minutes
        except KeyboardInterrupt:
            print(f"\n⏹️  Testing stopped by user after {test_count} attempts")
            break

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'continuous':
        continuous_function_testing()
    else:
        success, status = test_cloud_function_directly()
        if success:
            print(f"\n🎉 The website is ready to use!")
        else:
            print(f"\n⏳ Not ready yet: {status}")
            print(f"💡 Use 'python3 test_cloud_function_directly.py continuous' for continuous monitoring")
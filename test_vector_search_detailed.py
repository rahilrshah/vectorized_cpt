#!/usr/bin/env python3

import requests
import json
import time
import sys

def test_detailed_vector_search():
    """Test the Cloud Function with detailed analysis"""
    print("="*80)
    print("🧪 DETAILED VECTOR SEARCH DIAGNOSTIC")
    print("="*80)
    
    function_url = "https://us-central1-cpt-code-vectorized-dataset.cloudfunctions.net/findSimilarCptCodes"
    
    # Test with different types of medical procedures
    test_cases = [
        {
            "name": "Knee Surgery (Known in Database)",
            "text": "Bilateral total knee arthroplasty with patellar resurfacing"
        },
        {
            "name": "Simple Procedure",
            "text": "Removal of skin lesion"
        },
        {
            "name": "Heart Surgery",
            "text": "Coronary artery bypass"
        },
        {
            "name": "Exact CPT Description",
            "text": "Glossectomy; partial, with unilateral radical neck dissection"
        }
    ]
    
    results = []
    
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
                timeout=120
            )
            end_time = time.time()
            
            print(f"⏱️  Response time: {end_time - start_time:.2f}s")
            print(f"📊 HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS!")
                
                if 'result' in result:
                    if 'results' in result['result']:
                        matches = result['result']['results']
                        print(f"🎯 Found {len(matches)} matches")
                        
                        # Show top matches
                        for j, match in enumerate(matches[:3]):
                            cpt = match.get('CPT Codes', match.get('cpt_code', 'N/A'))
                            desc = match.get('Descriptions', match.get('description', 'N/A'))
                            print(f"   {j+1}. CPT {cpt}: {desc[:60]}...")
                        
                        results.append({
                            'test': test_case['name'],
                            'matches': len(matches),
                            'success': True
                        })
                    else:
                        # Check for error messages
                        if 'message' in result['result']:
                            print(f"📢 Message: {result['result']['message']}")
                        if 'status' in result['result']:
                            print(f"📊 Status: {result['result']['status']}")
                        
                        results.append({
                            'test': test_case['name'],
                            'matches': 0,
                            'success': False,
                            'message': result['result'].get('message', 'No message')
                        })
                else:
                    print(f"📦 Unexpected result format: {result}")
                    results.append({
                        'test': test_case['name'],
                        'matches': 0,
                        'success': False,
                        'message': 'Unexpected format'
                    })
            else:
                print(f"❌ HTTP Error {response.status_code}")
                error_text = response.text[:200]
                print(f"Error: {error_text}")
                results.append({
                    'test': test_case['name'],
                    'matches': 0,
                    'success': False,
                    'message': f"HTTP {response.status_code}: {error_text}"
                })
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append({
                'test': test_case['name'],
                'matches': 0,
                'success': False,
                'message': f"Exception: {e}"
            })
        
        # Small delay between tests
        if i < len(test_cases):
            print("⏸️  Waiting 3 seconds before next test...")
            time.sleep(3)
    
    # Summary
    print("\n" + "="*80)
    print("📊 DETAILED TEST SUMMARY")
    print("="*80)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    total_matches = sum(r['matches'] for r in results)
    
    print(f"Total tests: {total_tests}")
    print(f"Successful responses: {successful_tests}/{total_tests}")
    print(f"Total matches found: {total_matches}")
    
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        matches = f"({result['matches']} matches)" if result['success'] else f"({result['message']})"
        print(f"  {status} {result['test']}: {matches}")
    
    # Analysis
    print(f"\n🔍 ANALYSIS:")
    if total_matches == 0:
        print("🚨 NO MATCHES FOUND IN ANY TEST")
        print("   This confirms the vector search is not working")
        print("   Possible causes:")
        print("   1. Vector index still building (unlikely after 1.5 hours)")
        print("   2. Index field name mismatch") 
        print("   3. Vector search API issue")
        print("   4. Embedding compatibility problem")
    elif total_matches > 0:
        print("🎉 VECTOR SEARCH IS WORKING!")
        print(f"   Found matches in {sum(1 for r in results if r['matches'] > 0)} out of {total_tests} tests")
    
    # Check for consistent error messages
    error_messages = [r.get('message', '') for r in results if not r['success']]
    if error_messages:
        unique_errors = list(set(error_messages))
        if len(unique_errors) == 1 and 'initializing' in unique_errors[0]:
            print("🕐 All tests show 'initializing' message - index may still be building")
        else:
            print(f"🔍 Various error types found: {len(unique_errors)} different messages")

if __name__ == '__main__':
    test_detailed_vector_search()
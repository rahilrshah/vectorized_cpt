#!/usr/bin/env python3

import requests
import json

def test_with_exact_cpt():
    """Test with exact CPT description from database"""
    print("="*80)
    print("🧪 TESTING WITH EXACT CPT DESCRIPTION")
    print("="*80)
    
    function_url = "https://us-central1-cpt-code-vectorized-dataset.cloudfunctions.net/findSimilarCptCodes"
    
    # Use the exact description from database (CPT 41135)
    test_data = {
        "data": {
            "text": "Glossectomy; partial, with unilateral radical neck dissection"
        }
    }
    
    print(f"Testing with exact database text:")
    print(f"'{test_data['data']['text']}'")
    print(f"Expected to match CPT 41135")
    print("-" * 60)
    
    try:
        response = requests.post(
            function_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=120
        )
        
        print(f"📊 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'result' in result and 'results' in result['result']:
                matches = result['result']['results']
                print(f"🎯 Found {len(matches)} matches!")
                
                if len(matches) > 0:
                    print("🎉 SUCCESS! Vector search is working!")
                    for i, match in enumerate(matches[:5]):
                        cpt = match.get('CPT Codes', 'N/A')
                        desc = match.get('Descriptions', 'N/A')
                        print(f"   {i+1}. CPT {cpt}: {desc[:60]}...")
                else:
                    print("❌ Still 0 results even with exact text")
            else:
                print("❌ Unexpected response format")
                print(f"Response: {result}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_with_exact_cpt()
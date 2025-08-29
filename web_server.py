#!/usr/bin/env python3
"""
Flask web server for CPT Code Search using Vertex AI Vector Search
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import sys
from vertex_vector_search import search_cpt_codes, check_vertex_status

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Search for CPT codes"""
    try:
        data = request.get_json()
        query_text = data.get('text', '').strip()
        
        if not query_text:
            return jsonify({
                'success': False,
                'error': 'Please provide a medical procedure description'
            })
        
        print(f"🔍 Search request: '{query_text}'")
        
        # Use the working Vertex AI search
        results = search_cpt_codes(query_text, num_results=20)
        
        if results:
            # Format results for the frontend
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'cpt_code': result.get('cpt_code', 'N/A'),
                    'description': result.get('description', 'No description available'),
                    'category': result.get('category', ''),
                    'similarity': round(result.get('similarity', 0), 4),
                    'status': result.get('status', '')
                })
            
            print(f"✅ Found {len(formatted_results)} results")
            
            return jsonify({
                'success': True,
                'results': formatted_results,
                'query': query_text
            })
        else:
            print("⚠️  No results found")
            return jsonify({
                'success': True,
                'results': [],
                'message': 'No matching CPT codes found for this procedure',
                'query': query_text
            })
            
    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}'
        })

@app.route('/status')
def status():
    """Check system status"""
    try:
        vertex_status = check_vertex_status()
        return jsonify({
            'success': True,
            'vertex_ai': vertex_status,
            'system': 'operational'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'system': 'error'
        })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'CPT Vector Search'
    })

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 STARTING CPT CODE SEARCH WEB SERVER")
    print("=" * 80)
    
    # Check Vertex AI status
    try:
        status = check_vertex_status()
        print(f"📊 Vertex AI Status: {status['status']}")
        print(f"📋 Message: {status['message']}")
    except Exception as e:
        print(f"⚠️  Could not check Vertex AI status: {e}")
    
    port = int(os.environ.get('PORT', 8080))
    host = '0.0.0.0'  # Allow external connections
    
    print(f"\n🌐 Server starting on http://{host}:{port}")
    print(f"📱 Access the web interface at: http://localhost:{port}")
    print(f"🔍 API endpoint: http://localhost:{port}/search")
    print(f"📊 Status endpoint: http://localhost:{port}/status")
    print("\n💡 Ready to search CPT codes! Try queries like:")
    print("   - 'knee surgery arthroscopy'")
    print("   - 'coronary artery bypass'")
    print("   - 'skin lesion removal'")
    
    app.run(host=host, port=port, debug=False)
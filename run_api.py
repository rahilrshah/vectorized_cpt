#!/usr/bin/env python3
"""
Simple script to run the Medical Billing API
Handles basic setup and starts the FastAPI server
"""

import os
import sys
import subprocess
import time

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn', 
        'pydantic',
        'google-cloud-firestore'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    return missing

def install_dependencies():
    """Install missing dependencies"""
    print("📦 Installing required dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def run_structure_test():
    """Run the structure test to verify everything is working"""
    print("🧪 Running structure test...")
    try:
        result = subprocess.run([sys.executable, 'simple_test.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Structure test passed")
            return True
        else:
            print("❌ Structure test failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Could not run structure test: {e}")
        return False

def start_api_server(host="0.0.0.0", port=8000, reload=True):
    """Start the FastAPI server"""
    print(f"🚀 Starting Medical Billing API server...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Reload: {reload}")
    print()
    print(f"🌐 API will be available at:")
    print(f"   • Main interface: http://localhost:{port}")
    print(f"   • API docs: http://localhost:{port}/api/docs")
    print(f"   • Health check: http://localhost:{port}/api/v1/health")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Use uvicorn to run the FastAPI app
        cmd = [
            sys.executable, '-m', 'uvicorn',
            'app.main:app',
            '--host', host,
            '--port', str(port)
        ]
        
        if reload:
            cmd.append('--reload')
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")

def main():
    """Main function to set up and run the API"""
    print("🏥 Medical Billing API - Startup Script")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('app/main.py'):
        print("❌ Error: Please run this script from the project root directory")
        print("   Expected to find: app/main.py")
        sys.exit(1)
    
    # Check for missing dependencies
    missing_deps = check_dependencies()
    
    if missing_deps:
        print(f"⚠️ Missing dependencies: {', '.join(missing_deps)}")
        
        if os.path.exists('requirements.txt'):
            install_choice = input("Install missing dependencies? (y/n): ").lower().strip()
            if install_choice in ['y', 'yes']:
                if not install_dependencies():
                    print("❌ Cannot proceed without dependencies")
                    sys.exit(1)
            else:
                print("❌ Cannot run without required dependencies")
                sys.exit(1)
        else:
            print("❌ requirements.txt not found. Cannot install dependencies.")
            sys.exit(1)
    
    # Run structure test
    if not run_structure_test():
        print("❌ Structure test failed. Please fix issues before starting server.")
        continue_anyway = input("Continue anyway? (y/n): ").lower().strip()
        if continue_anyway not in ['y', 'yes']:
            sys.exit(1)
    
    print()
    print("🎉 System ready!")
    print()
    
    # Get server configuration
    try:
        port = int(input("Port (default 8000): ") or "8000")
    except ValueError:
        port = 8000
    
    host = input("Host (default 0.0.0.0): ") or "0.0.0.0"
    
    reload_choice = input("Enable auto-reload for development? (y/n, default y): ").lower().strip()
    reload = reload_choice not in ['n', 'no']
    
    print()
    
    # Start the server
    start_api_server(host=host, port=port, reload=reload)

if __name__ == "__main__":
    main()
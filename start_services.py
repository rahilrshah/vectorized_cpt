#!/usr/bin/env python3
"""
Start All Microservices
Development script to start all microservices and the API Gateway
"""

import subprocess
import sys
import time
import os
import signal
import threading
from typing import List, Dict
import requests

class ServiceManager:
    """Manages starting and stopping all microservices"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.services = [
            {
                "name": "Medical Processor API",
                "module": "api_services.medical_processor.main",
                "port": 8001,
                "path": "api_services/medical_processor"
            },
            {
                "name": "CPT Search API", 
                "module": "api_services.cpt_search.main",
                "port": 8002,
                "path": "api_services/cpt_search"
            },
            {
                "name": "Medical Coding API",
                "module": "api_services.medical_coding.main", 
                "port": 8003,
                "path": "api_services/medical_coding"
            },
            {
                "name": "API Gateway",
                "module": "api_gateway.main",
                "port": 8000,
                "path": "api_gateway"
            }
        ]
    
    def check_port(self, port: int) -> bool:
        """Check if a port is available"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result != 0  # Port is available if connection fails
        except:
            return True
    
    def wait_for_service(self, port: int, timeout: int = 30) -> bool:
        """Wait for a service to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=1)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(1)
        return False
    
    def start_service(self, service: Dict) -> subprocess.Popen:
        """Start a single service"""
        print(f"🚀 Starting {service['name']} on port {service['port']}...")
        
        # Check if port is available
        if not self.check_port(service['port']):
            print(f"⚠️  Port {service['port']} is already in use. Skipping {service['name']}.")
            return None
        
        # Start the service
        try:
            env = os.environ.copy()
            env['PYTHONPATH'] = os.getcwd()
            
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                f"{service['module']}:app",
                "--host", "0.0.0.0",
                "--port", str(service['port']),
                "--reload"
            ], env=env, cwd=os.getcwd())
            
            return process
            
        except Exception as e:
            print(f"❌ Failed to start {service['name']}: {e}")
            return None
    
    def start_all(self):
        """Start all services"""
        print("🏥 Starting Vectorized CPT Microservices...")
        print("=" * 60)
        
        # Start services (API Gateway last)
        for service in self.services:
            process = self.start_service(service)
            if process:
                self.processes.append(process)
                
                # Give each service time to start
                time.sleep(3)
                
                # Wait for health check (except for API Gateway which may depend on others)
                if service['port'] != 8000:
                    if self.wait_for_service(service['port'], 20):
                        print(f"✅ {service['name']} is healthy")
                    else:
                        print(f"⚠️  {service['name']} health check failed")
                else:
                    # Special handling for API Gateway
                    time.sleep(5)  # Give it more time to connect to services
                    print(f"✅ {service['name']} started")
        
        print("\n" + "=" * 60)
        print("🎉 All services started!")
        print("\nService Endpoints:")
        print("- Medical Processor API: http://localhost:8001")
        print("- CPT Search API:       http://localhost:8002")  
        print("- Medical Coding API:   http://localhost:8003")
        print("- API Gateway:          http://localhost:8000")
        print("\nAPI Gateway Docs:       http://localhost:8000/docs")
        print("Health Check:           http://localhost:8000/health")
        print("\n💡 Tip: Set VECTORIZED_CPT_API_KEY environment variable to use API mode")
        print("💡 Tip: Press Ctrl+C to stop all services")
        
        # Keep services running
        try:
            while True:
                time.sleep(1)
                # Check if any process has died
                for i, process in enumerate(self.processes):
                    if process and process.poll() is not None:
                        service_name = self.services[i]['name']
                        print(f"❌ {service_name} has stopped unexpectedly")
        
        except KeyboardInterrupt:
            print("\n🛑 Shutting down all services...")
            self.stop_all()
    
    def stop_all(self):
        """Stop all services"""
        for i, process in enumerate(self.processes):
            if process and process.poll() is None:
                service_name = self.services[i]['name']
                print(f"🛑 Stopping {service_name}...")
                
                try:
                    # Try graceful shutdown first
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    process.kill()
                    process.wait()
        
        print("✅ All services stopped")
    
    def status(self):
        """Check status of all services"""
        print("🏥 Vectorized CPT Services Status:")
        print("=" * 50)
        
        for service in self.services:
            port = service['port']
            name = service['name']
            
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    status = "🟢 HEALTHY"
                else:
                    status = f"🟡 HTTP {response.status_code}"
            except requests.exceptions.ConnectionError:
                status = "🔴 OFFLINE"
            except Exception as e:
                status = f"🟡 ERROR: {str(e)[:20]}"
            
            print(f"{name:25} (port {port}): {status}")


def create_api_key_example():
    """Create an example API key for testing"""
    print("\n📋 Creating Example API Key...")
    
    # This would normally be done through an admin interface
    # For now, we'll create a simple example
    try:
        from api_gateway.auth import api_key_manager
        
        api_key, key_id = api_key_manager.generate_api_key(
            user_id="example_user",
            rate_limit_per_hour=1000,
            expires_days=None  # Never expires
        )
        
        print(f"\n🔑 Example API Key Created:")
        print(f"   API Key: {api_key}")
        print(f"   Key ID:  {key_id}")
        print(f"\n💡 To use this key:")
        print(f"   export VECTORIZED_CPT_API_KEY={api_key}")
        print(f"   or add it to your .env file")
        
        return api_key, key_id
        
    except Exception as e:
        print(f"❌ Failed to create API key: {e}")
        return None, None


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage Vectorized CPT Microservices")
    parser.add_argument("command", choices=["start", "stop", "status", "create-key"], 
                       help="Command to execute")
    
    args = parser.parse_args()
    
    manager = ServiceManager()
    
    if args.command == "start":
        # Set up signal handler for clean shutdown
        def signal_handler(sig, frame):
            print("\n🛑 Received interrupt signal...")
            manager.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        manager.start_all()
        
    elif args.command == "stop":
        manager.stop_all()
        
    elif args.command == "status":
        manager.status()
        
    elif args.command == "create-key":
        create_api_key_example()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Complete System Startup Script
Starts all microservices, API Gateway, and web interface together
"""

import subprocess
import sys
import time
import os
import signal
import threading
from typing import List, Dict
import requests

class CompleteSystemManager:
    """Manages the complete Vectorized CPT system"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.services = [
            {
                "name": "Medical Processor API",
                "module": "api_services.medical_processor.main",
                "port": 8001,
                "health_url": "http://localhost:8001/health"
            },
            {
                "name": "CPT Search API", 
                "module": "api_services.cpt_search.main",
                "port": 8002,
                "health_url": "http://localhost:8002/health"
            },
            {
                "name": "Medical Coding API",
                "module": "api_services.medical_coding.main", 
                "port": 8003,
                "health_url": "http://localhost:8003/health"
            },
            {
                "name": "API Gateway",
                "module": "api_gateway.main",
                "port": 8000,
                "health_url": "http://localhost:8000/health"
            },
            {
                "name": "Web Interface",
                "module": "web_server_api",
                "port": 8080,
                "health_url": "http://localhost:8080/api/status"
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
    
    def wait_for_service(self, health_url: str, timeout: int = 30) -> bool:
        """Wait for a service to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(2)
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
            
            if service['name'] == 'Web Interface':
                # Special handling for web interface
                process = subprocess.Popen([
                    sys.executable, "-m", "uvicorn", 
                    f"{service['module']}:app",
                    "--host", "0.0.0.0",
                    "--port", str(service['port']),
                    "--reload"
                ], env=env, cwd=os.getcwd())
            else:
                # Standard microservice
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
    
    def create_example_api_key(self):
        """Create an example API key for testing"""
        print("\n🔑 Creating example API key...")
        
        try:
            # Give API Gateway time to start
            time.sleep(5)
            
            from api_gateway.auth import api_key_manager
            
            api_key, key_id = api_key_manager.generate_api_key(
                user_id="demo_user",
                rate_limit_per_hour=1000,
                expires_days=None  # Never expires
            )
            
            print(f"\n✅ Example API Key Created:")
            print(f"   API Key: {api_key}")
            print(f"   Key ID:  {key_id}")
            print(f"\n💡 Save this key for testing:")
            print(f"   export VECTORIZED_CPT_API_KEY={api_key}")
            
            # Save to file for convenience
            with open('.env.example', 'w') as f:
                f.write(f"VECTORIZED_CPT_API_KEY={api_key}\n")
                f.write(f"VECTORIZED_CPT_MODE=api\n")
                f.write(f"VECTORIZED_CPT_GATEWAY_URL=http://localhost:8000\n")
            
            print(f"   📄 Also saved to .env.example file")
            
            return api_key, key_id
            
        except Exception as e:
            print(f"❌ Failed to create API key: {e}")
            return None, None
    
    def start_all_services(self):
        """Start all services in the correct order"""
        print("🏥 Starting Complete Vectorized CPT System")
        print("=" * 80)
        
        # Start microservices first (except API Gateway)
        microservices = [s for s in self.services if s['name'] != 'API Gateway' and s['name'] != 'Web Interface']
        
        for service in microservices:
            process = self.start_service(service)
            if process:
                self.processes.append(process)
                # Give each service time to start
                time.sleep(3)
                
                # Wait for health check
                if self.wait_for_service(service['health_url'], 20):
                    print(f"✅ {service['name']} is healthy")
                else:
                    print(f"⚠️  {service['name']} health check failed")
        
        # Start API Gateway after microservices are ready
        api_gateway = next(s for s in self.services if s['name'] == 'API Gateway')
        gateway_process = self.start_service(api_gateway)
        if gateway_process:
            self.processes.append(gateway_process)
            time.sleep(3)
            
            if self.wait_for_service(api_gateway['health_url'], 20):
                print(f"✅ {api_gateway['name']} is healthy")
            else:
                print(f"⚠️  {api_gateway['name']} health check failed")
        
        # Create example API key in background
        key_thread = threading.Thread(target=self.create_example_api_key)
        key_thread.daemon = True
        key_thread.start()
        
        # Start Web Interface last
        web_interface = next(s for s in self.services if s['name'] == 'Web Interface')
        web_process = self.start_service(web_interface)
        if web_process:
            self.processes.append(web_process)
            time.sleep(3)
            
            if self.wait_for_service(web_interface['health_url'], 20):
                print(f"✅ {web_interface['name']} is healthy")
            else:
                print(f"⚠️  {web_interface['name']} health check failed")
        
        print("\n" + "=" * 80)
        print("🎉 Complete System Started!")
        print("\n🌐 Service URLs:")
        print("- Medical Processor:    http://localhost:8001/docs")
        print("- CPT Search:          http://localhost:8002/docs") 
        print("- Medical Coding:      http://localhost:8003/docs")
        print("- API Gateway:         http://localhost:8000/docs")
        print("- Web Interface:       http://localhost:8080")
        print("\n📊 Monitoring:")
        print("- System Health:       http://localhost:8080/#health")
        print("- Usage Analytics:     http://localhost:8080/#usage")
        print("- Complete Workflow:   http://localhost:8080/#workflow")
        print("\n🧪 Testing:")
        print("- Run integration tests: python test_web_integration.py")
        print("- Test individual services: http://localhost:8080/#testing")
        print("\n💡 Tips:")
        print("- Use the generated API key in the web interface")
        print("- Check .env.example for environment variables")
        print("- Press Ctrl+C to stop all services")
        
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
            print("\n🛑 Shutting down complete system...")
            self.stop_all_services()
    
    def stop_all_services(self):
        """Stop all services"""
        print("🛑 Stopping all services...")
        
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
    
    def run_integration_tests(self):
        """Run comprehensive integration tests"""
        print("🧪 Running Integration Tests...")
        print("=" * 60)
        
        # Give services time to fully start
        print("⏳ Waiting for services to be ready...")
        time.sleep(10)
        
        try:
            import asyncio
            from test_web_integration import WebIntegrationTester
            
            async def run_tests():
                tester = WebIntegrationTester("http://localhost:8080")
                results = await tester.run_all_tests()
                return results
            
            results = asyncio.run(run_tests())
            
            if results["failed"] == 0:
                print(f"\n🎉 All tests passed! System is fully functional.")
            else:
                print(f"\n⚠️  {results['failed']} tests failed. Check logs above.")
            
            return results["failed"] == 0
            
        except Exception as e:
            print(f"❌ Integration tests failed: {e}")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Complete System Manager")
    parser.add_argument("command", choices=["start", "test", "start-and-test"], 
                       help="Command to execute")
    
    args = parser.parse_args()
    
    manager = CompleteSystemManager()
    
    # Set up signal handler for clean shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Received interrupt signal...")
        manager.stop_all_services()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.command == "start":
        manager.start_all_services()
    
    elif args.command == "test":
        # Just run tests (assumes services are already running)
        success = manager.run_integration_tests()
        sys.exit(0 if success else 1)
    
    elif args.command == "start-and-test":
        # Start services in background and run tests
        import threading
        
        # Start services in background thread
        service_thread = threading.Thread(target=manager.start_all_services)
        service_thread.daemon = True
        service_thread.start()
        
        # Wait for services to start
        time.sleep(30)
        
        # Run tests
        success = manager.run_integration_tests()
        
        # Stop services
        manager.stop_all_services()
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
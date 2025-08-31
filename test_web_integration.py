#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Vectorized CPT Web Integration
Tests all web API endpoints and microservices integration
"""

import asyncio
import json
import os
import time
import base64
from typing import Dict, Any, List

import httpx
import pytest


class WebIntegrationTester:
    """Comprehensive test suite for the web API integration"""
    
    def __init__(self, base_url: str = "http://localhost:8080", api_key: str = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("VECTORIZED_CPT_API_KEY")
        self.test_results = []
        
        # Test data
        self.sample_medical_text = (
            "Patient underwent bilateral total knee arthroplasty with computer-assisted navigation. "
            "General anesthesia was administered. Post-operative pain management included epidural catheter. "
            "Patient also received prophylactic antibiotics and DVT prophylaxis. "
            "Procedure was uncomplicated with excellent range of motion achieved."
        )
        
        self.sample_procedures = "Bilateral total knee arthroplasty, computer-assisted navigation"
        
        self.sample_primary_codes = [
            {
                "cpt_code": "27447",
                "description": "Arthroplasty, knee, condyle and plateau; medial AND lateral compartments with or without patella resurfacing (total knee arthroplasty)",
                "similarity_score": 0.95
            }
        ]
    
    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": time.time(),
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
    
    async def test_web_server_health(self) -> bool:
        """Test if web server is running and healthy"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/status")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("Web Server Health", True, "Web server is running", data)
                    return True
                else:
                    self.log_test("Web Server Health", False, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_test("Web Server Health", False, str(e))
            return False
    
    async def test_api_key_configuration(self) -> bool:
        """Test API key configuration endpoint"""
        if not self.api_key:
            self.log_test("API Key Configuration", False, "No API key provided")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/api/configure",
                    json={"api_key": self.api_key}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("success", False)
                    message = data.get("message", "Unknown response")
                    
                    self.log_test("API Key Configuration", success, message, data)
                    return success
                else:
                    self.log_test("API Key Configuration", False, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_test("API Key Configuration", False, str(e))
            return False
    
    async def test_complete_workflow(self) -> bool:
        """Test complete medical coding workflow"""
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.base_url}/api/workflow",
                    json={
                        "text": self.sample_medical_text,
                        "max_results": 10,
                        "api_key": self.api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("success", False)
                    
                    if success:
                        # Verify workflow steps
                        required_steps = [
                            "step1_extracted_text",
                            "step2_extracted_procedures", 
                            "step3_cpt_results"
                        ]
                        
                        missing_steps = [step for step in required_steps if not data.get(step)]
                        
                        if missing_steps:
                            self.log_test("Complete Workflow", False, f"Missing steps: {missing_steps}")
                            return False
                        
                        cpt_count = len(data.get("step3_cpt_results", []))
                        processing_time = data.get("total_processing_time_ms", 0)
                        
                        self.log_test(
                            "Complete Workflow", 
                            True, 
                            f"Found {cpt_count} CPT codes in {processing_time}ms",
                            {
                                "cpt_count": cpt_count,
                                "processing_time": processing_time,
                                "services_used": data.get("services_used", [])
                            }
                        )
                        return True
                    else:
                        error = data.get("error", "Unknown error")
                        self.log_test("Complete Workflow", False, error)
                        return False
                else:
                    self.log_test("Complete Workflow", False, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_test("Complete Workflow", False, str(e))
            return False
    
    async def test_medical_text_processing(self) -> bool:
        """Test medical text processing service"""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/api/test/extract",
                    json={
                        "text": self.sample_medical_text,
                        "api_key": self.api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("success", False)
                    
                    if success:
                        extracted_data = data.get("data", {})
                        procedures = extracted_data.get("extracted_procedures", "")
                        
                        self.log_test(
                            "Medical Text Processing",
                            True,
                            f"Extracted procedures: {procedures[:50]}...",
                            extracted_data
                        )
                        return True
                    else:
                        self.log_test("Medical Text Processing", False, data.get("error", "Unknown error"))
                        return False
                else:
                    self.log_test("Medical Text Processing", False, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_test("Medical Text Processing", False, str(e))
            return False
    
    async def test_cpt_search(self) -> bool:
        """Test CPT code search service"""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/api/test/search",
                    json={
                        "text": self.sample_procedures,
                        "max_results": 10,
                        "api_key": self.api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("success", False)
                    
                    if success:
                        search_data = data.get("data", {})
                        results = search_data.get("results", [])
                        
                        self.log_test(
                            "CPT Search",
                            True,
                            f"Found {len(results)} CPT codes",
                            {"result_count": len(results), "top_result": results[0] if results else None}
                        )
                        return True
                    else:
                        self.log_test("CPT Search", False, data.get("error", "Unknown error"))
                        return False
                else:
                    self.log_test("CPT Search", False, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_test("CPT Search", False, str(e))
            return False
    
    async def test_comprehensive_coding(self) -> bool:
        """Test comprehensive medical coding service"""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                form_data = {
                    "primary_codes": json.dumps(self.sample_primary_codes),
                    "medical_text": self.sample_procedures,
                    "original_note": self.sample_medical_text,
                    "api_key": self.api_key
                }
                
                response = await client.post(
                    f"{self.base_url}/api/test/coding",
                    data=form_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("success", False)
                    
                    if success:
                        coding_data = data.get("data", {})
                        
                        # Count different types of codes found
                        anesthesia_count = len(coding_data.get("anesthesia_codes", []))
                        modifier_count = len(coding_data.get("modifiers", []))
                        related_count = len(coding_data.get("related_codes", []))
                        
                        self.log_test(
                            "Comprehensive Coding",
                            True,
                            f"Found {anesthesia_count} anesthesia, {modifier_count} modifiers, {related_count} related codes",
                            {
                                "anesthesia_count": anesthesia_count,
                                "modifier_count": modifier_count,
                                "related_count": related_count
                            }
                        )
                        return True
                    else:
                        self.log_test("Comprehensive Coding", False, data.get("error", "Unknown error"))
                        return False
                else:
                    self.log_test("Comprehensive Coding", False, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_test("Comprehensive Coding", False, str(e))
            return False
    
    async def test_health_dashboard(self) -> bool:
        """Test health dashboard functionality"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.base_url}/api/health")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("success") is False:
                        self.log_test("Health Dashboard", False, data.get("error", "Health check failed"))
                        return False
                    
                    services = data.get("services_status", {})
                    total_services = data.get("total_services", 0)
                    healthy_services = data.get("healthy_services", 0)
                    
                    self.log_test(
                        "Health Dashboard",
                        True,
                        f"{healthy_services}/{total_services} services healthy",
                        {
                            "total_services": total_services,
                            "healthy_services": healthy_services,
                            "services": list(services.keys())
                        }
                    )
                    return True
                else:
                    self.log_test("Health Dashboard", False, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_test("Health Dashboard", False, str(e))
            return False
    
    async def test_usage_analytics(self) -> bool:
        """Test usage analytics functionality"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.base_url}/api/usage")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    total_requests = data.get("total_requests", 0)
                    requests_this_hour = data.get("requests_this_hour", 0)
                    success_rate = (data.get("successful_requests", 0) / max(total_requests, 1)) * 100
                    
                    self.log_test(
                        "Usage Analytics",
                        True,
                        f"{total_requests} total, {requests_this_hour} this hour, {success_rate:.1f}% success rate",
                        data
                    )
                    return True
                else:
                    self.log_test("Usage Analytics", False, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_test("Usage Analytics", False, str(e))
            return False
    
    async def test_legacy_compatibility(self) -> bool:
        """Test legacy API compatibility"""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json={"text": "knee surgery"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("success", False)
                    
                    if success:
                        results = data.get("results", [])
                        self.log_test(
                            "Legacy Compatibility",
                            True,
                            f"Legacy search returned {len(results)} results",
                            {"result_count": len(results)}
                        )
                        return True
                    else:
                        self.log_test("Legacy Compatibility", False, data.get("error", "Legacy search failed"))
                        return False
                else:
                    self.log_test("Legacy Compatibility", False, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_test("Legacy Compatibility", False, str(e))
            return False
    
    async def test_performance_benchmarks(self) -> bool:
        """Test performance benchmarks"""
        try:
            # Test workflow performance with timing
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.base_url}/api/workflow",
                    json={
                        "text": self.sample_medical_text,
                        "max_results": 5,  # Smaller for speed
                        "api_key": self.api_key
                    }
                )
            
            end_time = time.time()
            total_time = (end_time - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                
                if success:
                    processing_time = data.get("total_processing_time_ms", 0)
                    
                    # Performance benchmarks
                    is_fast_enough = total_time < 30000  # 30 seconds max
                    
                    self.log_test(
                        "Performance Benchmark",
                        is_fast_enough,
                        f"Total: {total_time:.0f}ms, Processing: {processing_time}ms",
                        {
                            "total_time_ms": total_time,
                            "processing_time_ms": processing_time,
                            "within_benchmark": is_fast_enough
                        }
                    )
                    return is_fast_enough
                else:
                    self.log_test("Performance Benchmark", False, data.get("error", "Workflow failed"))
                    return False
            else:
                self.log_test("Performance Benchmark", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Performance Benchmark", False, str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        print("🧪 Starting Comprehensive Web Integration Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test sequence - order matters for dependencies
        tests = [
            ("Web Server Health", self.test_web_server_health),
            ("API Key Configuration", self.test_api_key_configuration),
            ("Health Dashboard", self.test_health_dashboard),
            ("Medical Text Processing", self.test_medical_text_processing),
            ("CPT Search", self.test_cpt_search),
            ("Comprehensive Coding", self.test_comprehensive_coding),
            ("Complete Workflow", self.test_complete_workflow),
            ("Usage Analytics", self.test_usage_analytics),
            ("Legacy Compatibility", self.test_legacy_compatibility),
            ("Performance Benchmark", self.test_performance_benchmarks),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test exception: {str(e)}")
                failed += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        summary = {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / len(tests)) * 100,
            "total_time_seconds": total_time,
            "test_results": self.test_results
        }
        
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Time: {total_time:.1f} seconds")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        print(f"\n🎯 Overall Status: {'✅ PASS' if failed == 0 else '❌ FAIL'}")
        
        return summary


async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Web Integration Testing Suite")
    parser.add_argument("--url", default="http://localhost:8080", help="Web server URL")
    parser.add_argument("--api-key", help="API key (or set VECTORIZED_CPT_API_KEY)")
    parser.add_argument("--json-output", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = WebIntegrationTester(args.url, args.api_key)
    
    # Run tests
    results = await tester.run_all_tests()
    
    # Save JSON output if requested
    if args.json_output:
        with open(args.json_output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {args.json_output}")
    
    # Exit with error code if tests failed
    if results["failed"] > 0:
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
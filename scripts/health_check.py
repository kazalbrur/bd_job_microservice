
# =============================================================================
# scripts/health_check.py
# Health check script for monitoring the application
# Can be used by load balancers, monitoring systems, or cron jobs
# =============================================================================

#!/usr/bin/env python3




import requests
import sys
import time
import json
import argparse
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self, base_url="http://localhost:8000", timeout=10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def check_health_endpoint(self):
        # Check the main health endpoint
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Health endpoint: OK")
                return True, data
            else:
                logger.error(f"❌ Health endpoint returned {response.status_code}")
                return False, {"error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Health endpoint failed: {e}")
            return False, {"error": str(e)}
    
    def check_api_endpoints(self):
        # Check critical API endpoints
        endpoints = [
            ("/jobs/", "Jobs listing"),
            ("/metrics", "Metrics"),
        ]
        
        results = {}
        
        for endpoint, description in endpoints:
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ {description}: OK")
                    results[endpoint] = {"status": "ok", "response_time": response.elapsed.total_seconds()}
                else:
                    logger.error(f"❌ {description}: HTTP {response.status_code}")
                    results[endpoint] = {"status": "error", "code": response.status_code}
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ {description}: {e}")
                results[endpoint] = {"status": "error", "error": str(e)}
        
        return results
    
    def check_database_health(self):
        # Check database connectivity through metrics endpoint
        try:
            response = self.session.get(
                f"{self.base_url}/metrics",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'total_jobs' in data and isinstance(data['total_jobs'], int):
                    logger.info("✅ Database connectivity: OK")
                    return True, data
                else:
                    logger.error("❌ Database connectivity: Invalid response")
                    return False, {"error": "Invalid metrics response"}
            else:
                logger.error(f"❌ Database connectivity: HTTP {response.status_code}")
                return False, {"error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Database connectivity: {e}")
            return False, {"error": str(e)}
    
    def check_response_times(self):
        # Check API response times
        endpoints = ["/health", "/jobs/", "/metrics"]
        response_times = {}
        
        for endpoint in endpoints:
            times = []
            for i in range(3):  # Test 3 times
                try:
                    start_time = time.time()
                    response = self.session.get(
                        f"{self.base_url}{endpoint}",
                        timeout=self.timeout
                    )
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        times.append((end_time - start_time) * 1000)  # Convert to ms
                    
                except requests.exceptions.RequestException:
                    pass
            
            if times:
                avg_time = sum(times) / len(times)
                response_times[endpoint] = {
                    "avg_ms": round(avg_time, 2),
                    "samples": len(times)
                }
                
                if avg_time < 500:
                    logger.info(f"✅ {endpoint} response time: {avg_time:.0f}ms")
                else:
                    logger.warning(f"⚠️ {endpoint} response time: {avg_time:.0f}ms (slow)")
            else:
                response_times[endpoint] = {"error": "No successful requests"}
                logger.error(f"❌ {endpoint}: No successful requests")
        
        return response_times
    
    def comprehensive_check(self):
        # Run all health checks
        logger.info(f"🔍 Starting health check for {self.base_url}")
        start_time = datetime.now()
        
        results = {
            "timestamp": start_time.isoformat(),
            "base_url": self.base_url,
            "checks": {}
        }
        
        # Main health check
        health_ok, health_data = self.check_health_endpoint()
        results["checks"]["health"] = {
            "status": "ok" if health_ok else "error",
            "data": health_data
        }
        
        # API endpoints check
        api_results = self.check_api_endpoints()
        results["checks"]["api_endpoints"] = api_results
        
        # Database check
        db_ok, db_data = self.check_database_health()
        results["checks"]["database"] = {
            "status": "ok" if db_ok else "error",
            "data": db_data
        }
        
        # Response time check
        response_times = self.check_response_times()
        results["checks"]["response_times"] = response_times
        
        # Overall status
        all_checks_passed = (
            health_ok and 
            db_ok and 
            all(check.get("status") == "ok" for check in api_results.values())
        )
        
        results["overall_status"] = "healthy" if all_checks_passed else "unhealthy"
        results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"🏁 Health check completed: {results['overall_status'].upper()}")
        
        return results

def main():
    parser = argparse.ArgumentParser(description="Health check for BD Jobs API")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the API")
    parser.add_argument("--timeout", type=int, default=10,
                       help="Request timeout in seconds")
    parser.add_argument("--json", action="store_true",
                       help="Output results in JSON format")
    parser.add_argument("--continuous", type=int, metavar="SECONDS",
                       help="Run continuously with specified interval")
    parser.add_argument("--fail-fast", action="store_true",
                       help="Exit with error code on first failure")
    
    args = parser.parse_args()
    
    checker = HealthChecker(base_url=args.url, timeout=args.timeout)
    
    def run_check():
        results = checker.comprehensive_check()
        
        if args.json:
            print(json.dumps(results, indent=2))
        
        if args.fail_fast and results["overall_status"] != "healthy":
            sys.exit(1)
        
        return results["overall_status"] == "healthy"
    
    if args.continuous:
        logger.info(f"🔄 Running continuous health checks every {args.continuous} seconds")
        try:
            while True:
                run_check()
                time.sleep(args.continuous)
        except KeyboardInterrupt:
            logger.info("🛑 Continuous health check stopped")
            sys.exit(0)
    else:
        success = run_check()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
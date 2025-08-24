#!/usr/bin/env python3
"""Security middleware validation script."""

import asyncio
import time
from typing import List, Tuple
import httpx
import redis
import subprocess
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from app.core.settings import get_settings


class SecurityMiddlewareTester:
    """Test security middleware functionality."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize tester with base URL."""
        self.base_url = base_url
        self.settings = get_settings()
        self.redis_client = redis.Redis.from_url(self.settings.redis_url)

    async def test_rate_limiting(self) -> Tuple[bool, str]:
        """Test rate limiting: make 101 requests/minute, verify 429 response."""
        print("🧪 Testing rate limiting...")

        # Clear any existing rate limit data
        self.redis_client.flushall()

        async with httpx.AsyncClient() as client:
            tasks = []
            # Make 101 requests (exceeding the 100/minute limit)
            for i in range(101):
                tasks.append(client.get(f"{self.base_url}/health"))

            # Execute requests concurrently to simulate rapid requests
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Count responses
            success_count = 0
            rate_limited_count = 0
            error_count = 0

            for response in responses:
                if isinstance(response, Exception):
                    error_count += 1
                    print(f"❌ Request error: {response}")
                elif response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    rate_limited_count += 1
                    print(f"✅ Rate limited request {rate_limited_count}: {response.status_code}")
                else:
                    print(f"⚠️  Unexpected status: {response.status_code}")

            print(f"📊 Results: {success_count} success, {rate_limited_count} rate limited, {error_count} errors")

            if rate_limited_count > 0:
                return True, f"✅ Rate limiting working: {rate_limited_count} requests were rate limited"
            else:
                return False, "❌ Rate limiting not working: no 429 responses received"

    async def test_penetration_detection(self) -> Tuple[bool, str]:
        """Test penetration detection with malicious requests."""
        print("🧪 Testing penetration detection...")

        # Clear Redis data
        self.redis_client.flushall()

        malicious_patterns = [
            "/admin.php",
            "/wp-admin",
            "/.env",
            "/config.json",
            "/../../../etc/passwd",
            "/api/users<script>alert(1)</script>",
            "/api/'; DROP TABLE users; --",
        ]

        async with httpx.AsyncClient() as client:
            banned = False
            attempt_count = 0

            for pattern in malicious_patterns:
                attempt_count += 1
                try:
                    response = await client.get(f"{self.base_url}{pattern}", timeout=5.0)
                    print(f"📡 Attempt {attempt_count}: {pattern} -> {response.status_code}")

                    if response.status_code == 403:
                        print("🚫 IP appears to be banned!")
                        banned = True
                        break

                except Exception as e:
                    print(f"📡 Attempt {attempt_count}: {pattern} -> Error: {e}")

                # Small delay between requests
                await asyncio.sleep(0.1)

            if banned:
                return True, f"✅ Penetration detection working: IP banned after {attempt_count} malicious attempts"
            else:
                return False, f"❌ Penetration detection not working: IP not banned after {attempt_count} attempts"

    def test_redis_integration(self) -> Tuple[bool, str]:
        """Test Redis integration for security data storage."""
        print("🧪 Testing Redis integration...")

        try:
            # Check if Redis is accessible
            self.redis_client.ping()
            print("✅ Redis connection successful")

            # Set a test security key
            test_key = "security:test:integration"
            test_value = "working"
            self.redis_client.setex(test_key, 60, test_value)

            # Retrieve it
            retrieved_value = self.redis_client.get(test_key)

            if retrieved_value and retrieved_value.decode() == test_value:
                print("✅ Redis set/get operations working")

                # Check security keys pattern
                security_keys = self.redis_client.keys("security:*")
                print(f"🔍 Found {len(security_keys)} security keys in Redis")

                for key in security_keys:
                    key_str = key.decode()
                    ttl = self.redis_client.ttl(key)
                    print(f"   - {key_str}: TTL={ttl}s")

                return True, f"✅ Redis integration working: {len(security_keys)} security keys found"
            else:
                return False, "❌ Redis set/get operations failed"

        except Exception as e:
            return False, f"❌ Redis connection failed: {e}"

    def test_security_logs(self) -> Tuple[bool, str]:
        """Test security logging functionality."""
        print("🧪 Testing security logs...")

        log_file = self.settings.security_log_file

        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    log_content = f.read()

                log_lines = log_content.strip().split('\n') if log_content else []
                print(f"📄 Found {len(log_lines)} log entries")

                if len(log_lines) > 0:
                    print("📋 Recent log entries:")
                    for line in log_lines[-5:]:  # Show last 5 entries
                        print(f"   {line}")

                    return True, f"✅ Security logging working: {len(log_lines)} log entries found"
                else:
                    return False, "❌ Security log file exists but is empty"

            except Exception as e:
                return False, f"❌ Error reading security log: {e}"
        else:
            return False, f"❌ Security log file not found: {log_file}"

    async def run_all_tests(self) -> dict:
        """Run all security middleware tests."""
        print("🚀 Starting comprehensive security middleware validation...\n")

        results = {}

        # Test Redis integration first
        results['redis'] = self.test_redis_integration()

        # Test rate limiting
        results['rate_limiting'] = await self.test_rate_limiting()

        # Test penetration detection
        results['penetration_detection'] = await self.test_penetration_detection()

        # Test security logs
        results['security_logs'] = self.test_security_logs()

        # Summary
        print("\n📊 Test Results Summary:")
        all_passed = True

        for test_name, (passed, message) in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test_name}: {status}")
            print(f"   {message}")
            print()

            if not passed:
                all_passed = False

        if all_passed:
            print("🎉 All security middleware tests PASSED!")
        else:
            print("⚠️  Some security middleware tests FAILED!")

        return results


async def main():
    """Main test runner."""
    print("🔒 AgentFlow Security Middleware Validation")
    print("=" * 50)

    # Check if API server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=2.0)
            if response.status_code == 200:
                print("✅ API server is running")
            else:
                print("⚠️  API server running but health check failed")
    except Exception as e:
        print(f"❌ API server not running: {e}")
        print("Please start the API server first:")
        print("   cd apps/api && uvicorn app.main:app --reload")
        sys.exit(1)

    # Run tests
    tester = SecurityMiddlewareTester()
    results = await tester.run_all_tests()

    # Exit with appropriate code
    if all(passed for passed, _ in results.values()):
        print("\n✅ Security middleware validation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Security middleware validation failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
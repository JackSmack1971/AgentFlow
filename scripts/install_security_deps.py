#!/usr/bin/env python3
"""Install security middleware dependencies."""

import subprocess
import sys
import os

def install_fastapi_guard():
    """Install fastapi-guard dependency."""
    print("🔧 Installing fastapi-guard dependency...")

    try:
        # Install fastapi-guard
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "fastapi-guard==3.0.2"
        ], capture_output=True, text=True, check=True)

        print("✅ fastapi-guard installed successfully")
        print(result.stdout)

        # Verify installation
        result = subprocess.run([
            sys.executable, "-c", "import fastapi_guard; print('fastapi-guard version:', fastapi_guard.__version__)"
        ], capture_output=True, text=True, check=True)

        print("✅ fastapi-guard import successful")
        print(result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install fastapi-guard: {e}")
        print("Error output:", e.stderr)
        sys.exit(1)

def check_redis_connection():
    """Check Redis connection for security middleware."""
    print("🔍 Checking Redis connection...")

    try:
        # Add the app directory to the path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

        from app.core.settings import get_settings
        import redis

        settings = get_settings()
        print(f"📋 Redis URL: {settings.redis_url}")

        # Test Redis connection
        redis_client = redis.Redis.from_url(settings.redis_url)
        redis_client.ping()

        print("✅ Redis connection successful")

        # Test security key operations
        test_key = "security:test:connection"
        redis_client.setex(test_key, 30, "test_value")
        value = redis_client.get(test_key)

        if value and value.decode() == "test_value":
            print("✅ Redis security key operations working")
            redis_client.delete(test_key)
        else:
            print("❌ Redis security key operations failed")

        return True

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Please ensure Redis is running and REDIS_URL is configured correctly")
        return False

def main():
    """Main installation and verification."""
    print("🚀 AgentFlow Security Middleware Setup")
    print("=" * 50)

    # Install dependencies
    install_fastapi_guard()

    print()

    # Check Redis connection
    redis_ok = check_redis_connection()

    print()

    if redis_ok:
        print("🎉 Security middleware setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Start the API server: cd apps/api && uvicorn app.main:app --reload")
        print("   2. Test security features: python scripts/test_security_middleware.py")
        print("   3. Monitor security logs: tail -f logs/security.log")
        print("   4. Check Redis security data: python scripts/check_redis_security.py")
    else:
        print("⚠️  Setup completed with warnings!")
        print("Please fix Redis connection before using security middleware.")

if __name__ == "__main__":
    main()
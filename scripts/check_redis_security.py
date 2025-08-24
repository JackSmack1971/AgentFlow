#!/usr/bin/env python3
"""Check Redis security data storage."""

import redis
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from app.core.settings import get_settings


def check_redis_security():
    """Check Redis security keys and data."""
    print("🔍 Checking Redis security data...")

    try:
        settings = get_settings()
        redis_client = redis.Redis.from_url(settings.redis_url)

        # Test connection
        redis_client.ping()
        print("✅ Redis connection successful")

        # Get all security keys
        security_keys = redis_client.keys("security:*")

        if not security_keys:
            print("ℹ️  No security keys found in Redis")
            return

        print(f"🔑 Found {len(security_keys)} security keys:")

        for key in security_keys:
            key_str = key.decode()
            ttl = redis_client.ttl(key)
            value = redis_client.get(key)

            if value:
                value_str = value.decode()
                print(f"   📋 {key_str}: '{value_str}' (TTL: {ttl}s)")
            else:
                print(f"   📋 {key_str}: (TTL: {ttl}s)")

        # Check specific security data types
        print("\n📊 Security Data Summary:")

        rate_limit_keys = redis_client.keys("security:rate_limit:*")
        ban_keys = redis_client.keys("security:ban:*")
        failed_attempt_keys = redis_client.keys("security:failed_attempts:*")

        print(f"   🚦 Rate limit entries: {len(rate_limit_keys)}")
        print(f"   🚫 Banned IPs: {len(ban_keys)}")
        print(f"   ⚠️  Failed attempt counters: {len(failed_attempt_keys)}")

        if len(ban_keys) > 0:
            print("\n🚫 Currently banned IPs:")
            for key in ban_keys:
                key_str = key.decode()
                ip = key_str.replace("security:ban:", "")
                ttl = redis_client.ttl(key)
                print(f"   🚫 {ip} (remaining: {ttl}s)")

    except Exception as e:
        print(f"❌ Redis error: {e}")
        sys.exit(1)


def clear_security_data():
    """Clear all security data from Redis."""
    print("🧹 Clearing Redis security data...")

    try:
        settings = get_settings()
        redis_client = redis.Redis.from_url(settings.redis_url)

        security_keys = redis_client.keys("security:*")
        if security_keys:
            redis_client.delete(*security_keys)
            print(f"✅ Cleared {len(security_keys)} security keys")
        else:
            print("ℹ️  No security keys to clear")

    except Exception as e:
        print(f"❌ Error clearing security data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_security_data()
    else:
        check_redis_security()
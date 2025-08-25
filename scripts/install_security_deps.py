#!/usr/bin/env python3
"""Install security middleware dependencies."""

import asyncio
import logging
import os
import re
import subprocess
import sys


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DependencyInstallationError(Exception):
    """Raised when a dependency cannot be installed."""


async def _run(cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
    """Run a subprocess command with timeout."""
    return await asyncio.wait_for(
        asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        ),
        timeout=timeout,
    )


async def install_fastapi_guard() -> None:
    """Install fastapi-guard dependency."""
    version = os.getenv("FASTAPI_GUARD_VERSION", "4.0.3")
    if not re.fullmatch(r"\d+(?:\.\d+)*", version):
        raise DependencyInstallationError("Invalid FASTAPI_GUARD_VERSION format")

    cmd = [sys.executable, "-m", "pip", "install", f"fastapi-guard=={version}"]
    for attempt in range(1, 4):
        try:
            result = await _run(cmd, 300)
            logger.info("fastapi-guard installation output: %s", result.stdout.strip())
            await _run([sys.executable, "-c", "import fastapi_guard"], 60)
            logger.info("fastapi-guard import check passed")
            return
        except Exception as exc:  # pragma: no cover - generic for safety
            logger.error("Attempt %d failed: %s", attempt, exc)
            if attempt == 3:
                raise DependencyInstallationError(
                    f"Failed to install fastapi-guard=={version}"
                ) from exc
            await asyncio.sleep(1)


async def check_redis_connection() -> bool:
    """Check Redis connection for security middleware."""
    logger.info("Checking Redis connection...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
        from app.core.settings import get_settings
        from redis.asyncio import Redis
        settings = get_settings()
        logger.info("Redis URL: %s", settings.redis_url)
        client = Redis.from_url(settings.redis_url)
        for attempt in range(1, 3):
            try:
                await asyncio.wait_for(client.ping(), timeout=5); break
            except Exception:
                if attempt == 2: raise
                await asyncio.sleep(1)
        await client.setex("security:test:connection", 30, "test_value")
        value = await client.get("security:test:connection")
        if value and value.decode() == "test_value":
            await client.delete("security:test:connection")
            logger.info("Redis security key operations working")
        else:
            logger.error("Redis security key operations failed")
        await client.close()
        return True
    except Exception as exc:  # pragma: no cover - fallback
        logger.error("Redis connection failed: %s", exc)
        logger.error("Ensure Redis is running and REDIS_URL is configured correctly")
        return False


async def main() -> None:
    """Main installation and verification."""
    logger.info("AgentFlow Security Middleware Setup")
    try:
        await install_fastapi_guard()
    except DependencyInstallationError as exc:
        logger.error("Dependency installation failed: %s", exc)
        return

    if await check_redis_connection():
        logger.info("Security middleware setup completed successfully!")
    else:
        logger.warning(
            "Setup completed with warnings. Fix Redis connection before use."
        )


if __name__ == "__main__":
    asyncio.run(main())


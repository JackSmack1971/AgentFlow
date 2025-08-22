from __future__ import annotations

import asyncio

import psycopg
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from ..config import Settings, get_settings
from ..exceptions import HealthCheckError
from ..models.health import HealthStatus

router = APIRouter()


async def check_postgres(dsn: str, timeout: float = 5.0) -> None:
    try:
        conn = await asyncio.wait_for(
            psycopg.AsyncConnection.connect(dsn),
            timeout,
        )
        await conn.execute("SELECT 1")
        await conn.close()
    except Exception as exc:  # noqa: BLE001
        raise HealthCheckError("postgres", str(exc)) from exc


async def check_redis(url: str, timeout: float = 5.0) -> None:
    client = aioredis.from_url(url, socket_connect_timeout=timeout)
    try:
        await asyncio.wait_for(client.ping(), timeout)
    except Exception as exc:  # noqa: BLE001
        raise HealthCheckError("redis", str(exc)) from exc
    finally:
        await client.close()


@router.get("/health", response_model=HealthStatus, tags=["health"])
async def health() -> HealthStatus:
    return HealthStatus(status="ok")


@router.get("/readiness", response_model=HealthStatus, tags=["health"])
async def readiness(
    settings: Settings = Depends(get_settings),
) -> HealthStatus:
    try:
        await asyncio.gather(
            check_postgres(settings.database_url),
            check_redis(settings.redis_url),
        )
    except HealthCheckError as exc:
        logger.error({"service": exc.service, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{exc.service} unavailable",
        ) from exc
    return HealthStatus(status="ready")

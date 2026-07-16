import redis.asyncio as redis

from app.config import settings
from app.logging_config import logger


redis_client = None


async def init_redis():
    global redis_client

    redis_client = redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
        health_check_interval=30
    )

    try:
        await redis_client.ping()
        logger.info("Redis connection established")

    except Exception as exc:
        logger.warning(
            f"Redis ping failed during startup: {exc}"
        )


async def close_redis():
    global redis_client

    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


async def get_cache(key: str):
    global redis_client

    if not redis_client:
        return None

    try:
        import asyncio
        return await asyncio.wait_for(redis_client.get(key), timeout=0.2)

    except asyncio.TimeoutError:
        logger.warning(
            "dependency_timeout",
            dependency="redis",
            operation="get",
            timeout_ms=200,
            key=key
        )
        return None
    except Exception as exc:
        logger.warning(
            f"Redis GET failed for key={key}: {exc}"
        )
        return None


async def set_cache(
    key: str,
    value: str,
    ttl_seconds: int = 300
):
    global redis_client

    if not redis_client:
        return

    try:
        import asyncio
        await asyncio.wait_for(
            redis_client.set(
                key,
                value,
                ex=ttl_seconds
            ),
            timeout=0.2
        )

    except asyncio.TimeoutError:
        logger.warning(
            "dependency_timeout",
            dependency="redis",
            operation="set",
            timeout_ms=200,
            key=key
        )
    except Exception as exc:
        logger.warning(
            f"Redis SET failed for key={key}: {exc}"
        )


async def delete_cache(key: str):
    global redis_client

    if not redis_client:
        return

    try:
        import asyncio
        await asyncio.wait_for(redis_client.delete(key), timeout=0.2)

    except asyncio.TimeoutError:
        logger.warning(
            "dependency_timeout",
            dependency="redis",
            operation="delete",
            timeout_ms=200,
            key=key
        )
    except Exception as exc:
        logger.warning(
            f"Redis DELETE failed for key={key}: {exc}"
        )
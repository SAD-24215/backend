from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings


def create_redis_client() -> Redis:
    password = settings.redis_password
    return Redis(
        host=settings.app_host,
        port=settings.redis_port,
        password=password.get_secret_value() if password is not None else None,
        decode_responses=True,
    )


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis

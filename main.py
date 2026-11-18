from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.features import auto_register_routers
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.redis import create_redis_client
from app.db.session import engine
import structlog


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with create_redis_client() as redis_client:
            app.state.redis = redis_client
            yield
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

    setup_logging()

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://localhost:\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    auto_register_routers(app)

    return app


if __name__ == "__main__":
    logger = structlog.get_logger(__name__)
    logger.info(f"Сервер запущен, {settings.app_host}:{settings.app_port}")

    uvicorn.run(
        "main:create_app",
        factory=True,
        host=settings.app_host,
        port=settings.app_port,
    )

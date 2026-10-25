from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.features import auto_register_routers
from app.config.config import settings
from app.config.logging_config import setup_logging
import structlog


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)

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
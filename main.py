from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.features import auto_register_routers
from app.config.config import settings


def init_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)

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
    app = init_app()
    uvicorn.run(app, host="127.0.0.1", port=8001)
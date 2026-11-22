import asyncio
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from getpass import getpass

import structlog
import uvicorn
from asyncpg.exceptions import PostgresError
from email_validator import EmailNotValidError, validate_email
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.consts.exceptions import LoginAlreadyExistsError
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.redis import create_redis_client
from app.db.session import engine, session_factory
from app.features import auto_register_routers
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


async def create_admin_user() -> None:
    """Запрашивает учётные данные и создаёт администратора в обеих БД."""
    try:
        test_url = settings.test_sqlalchemy_database_uri
    except ValueError as exc:
        raise SystemExit(str(exc)) from None

    try:
        email = validate_email(
            input("Email администратора: ").strip(), check_deliverability=False
        ).normalized
    except EmailNotValidError:
        raise SystemExit("Укажите действительный email.") from None

    if len(email) > 100:
        raise SystemExit("Email должен содержать не более 100 символов.")

    password = getpass("Пароль администратора: ")
    if not 1 <= len(password) <= 1024:
        raise SystemExit("Пароль должен содержать от 1 до 1024 символов.")

    test_engine = create_async_engine(test_url)
    failures: list[str] = []
    try:
        databases = (
            ("основной БД", session_factory),
            ("тестовой БД", async_sessionmaker(test_engine)),
        )
        for database, sessions in databases:
            try:
                async with sessions() as session:
                    repository = UserRepository(session)
                    service = UserService(repository)
                    try:
                        await service.add_employee(email, password, role="admin")
                    except LoginAlreadyExistsError:
                        async with session.begin():
                            user = await repository.get_by_email(email)
                            user_id = user.id if user is not None else None
                        if user_id is not None and await service.is_admin(user_id):
                            print(f"Администратор с этим email уже есть в {database}.")
                        else:
                            failures.append(
                                f"В {database} этот email занят другим пользователем."
                            )
                    else:
                        print(f"Администратор создан в {database}.")
            except (SQLAlchemyError, PostgresError, OSError) as exc:
                failures.append(
                    f"Не удалось создать администратора в {database} ({type(exc).__name__}). "
                    "Проверьте подключение и убедитесь, что миграции применены."
                )
    finally:
        await test_engine.dispose()
        await engine.dispose()

    if failures:
        raise SystemExit("\n".join(failures))


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with create_redis_client() as redis_client:
            app.state.redis = redis_client
            yield
    finally:
        await engine.dispose()


def mount_folder(app: FastAPI, path: str):
    app.mount(f"/{path}", StaticFiles(directory=path), name=path)


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

    mount_folder(app, settings.images_path)

    return app


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--create-admin",
        action="store_true",
        help="Создать администратора в основной и тестовой БД.",
    )
    if parser.parse_args().create_admin:
        asyncio.run(create_admin_user())
        raise SystemExit(0)

    logger = structlog.get_logger(__name__)
    logger.info(f"Сервер запущен, {settings.app_host}:{settings.app_port}")

    uvicorn.run(
        "main:create_app",
        factory=True,
        host=settings.app_host,
        port=settings.app_port,
    )

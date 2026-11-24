"""Эндпоинты регистрации, входа, обновления токенов и создания сотрудников."""

from math import ceil
from time import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from limits import RateLimitItemPerMinute
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.consts.dto import UserIdentity
from app.consts.exceptions import (
    ClassicCredentialsAlreadySetError,
    LoginAlreadyExistsError,
)
from app.core.config import settings
from app.core.jwt_tokens import (
    create_access_token,
    get_refresh_token,
    get_user_id_from_token,
    rotate_refresh_token,
)
from app.db.redis import get_redis
from app.db.session import get_session
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService

from .schemas import (
    AddEmployeePayload,
    EmployeeResponse,
    LoginPayload,
    RefreshAccessTokenResponse,
    RoleResponse,
    SignupPayload,
    SystemIdPayload,
    TokenResponse,
    TokenPayload,
)

router = APIRouter(tags=["user"])
login_limit = RateLimitItemPerMinute(5)
login_limiter = MovingWindowRateLimiter(MemoryStorage())
RedisClient = Annotated[Redis, Depends(get_redis)]
access_bearer = HTTPBearer(auto_error=False, bearerFormat="JWT")


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRepository:
    """Создаёт репозиторий пользователей с сессией БД текущего запроса."""
    return UserRepository(session)


def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    """Создаёт сервис пользователей с репозиторием текущего запроса."""
    return UserService(repository)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(access_bearer)],
) -> int:
    """Проверяет access-токен и возвращает ID пользователя из JWT."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    secret_key = settings.jwt_secret_key
    if secret_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token service is unavailable",
        )

    try:
        return get_user_id_from_token(
            credentials.credentials, secret_key=secret_key.get_secret_value()
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def require_admin(
    user_id: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    """Проверяет текущую роль пользователя в БД."""
    if not await service.is_admin(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator role required",
        )


async def token_response(
    identity: UserIdentity, secret_key: str, redis: Redis
) -> TokenResponse:
    """Собирает пару токенов и системный ID в ответ для клиента.

    Args:
        identity: Внутренний и системный идентификаторы пользователя.
        secret_key: Ключ подписи access-токена.
        redis: Клиент для сохранения refresh-токена.

    Raises:
        HTTPException: HTTP 503 при ошибке Redis.
    """
    access_token = create_access_token(identity.id, secret_key=secret_key)
    try:
        refresh_token = await get_refresh_token(redis, identity.id)
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token service is unavailable",
        ) from exc

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        system_id=identity.system_id,
    )


@router.post("/api/v1/users", status_code=status.HTTP_201_CREATED)
async def signup_classic(
    payload: SignupPayload,
    service: Annotated[UserService, Depends(get_user_service)],
    redis: RedisClient,
) -> TokenResponse:
    """Регистрирует новый аккаунт или привязывает email и пароль по системному ID.

    Returns:
        Пара токенов и системный ID пользователя.

    Raises:
        HTTPException: HTTP 401 при неверном системном ID или HTTP 409 при конфликте.
    """
    secret_key = settings.jwt_secret_key.get_secret_value()
    password = payload.password.get_secret_value()

    try:
        if payload.system_id is None:
            identity = await service.signup_without_id(payload.login, password)
        else:
            identity = await service.signup(
                payload.login, password, str(payload.system_id)
            )
    except LoginAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login already exists",
        ) from exc
    except ClassicCredentialsAlreadySetError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email and password are already set",
        ) from exc

    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid system ID"
        )

    return await token_response(identity, secret_key, redis)


async def limit_login_attempts(request: Request) -> None:
    """Ограничивает вход пятью запросами в минуту на IP и маршрут.

    Raises:
        HTTPException: HTTP 429 с заголовком Retry-After при превышении лимита.
    """
    client_ip = request.client.host if request.client else "unknown"
    if not login_limiter.hit(login_limit, request.url.path, client_ip):
        reset_time, _ = login_limiter.get_window_stats(
            login_limit, request.url.path, client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts",
            headers={"Retry-After": str(max(1, ceil(reset_time - time())))},
        )


@router.post("/api/v1/sessions", dependencies=[Depends(limit_login_attempts)])
async def login_classic(
    payload: LoginPayload,
    service: Annotated[UserService, Depends(get_user_service)],
    redis: RedisClient,
) -> TokenResponse:
    """Проверяет email и пароль и выдаёт пару токенов и системный ID.

    Raises:
        HTTPException: HTTP 401 при неверном email или пароле.
    """
    secret_key = settings.jwt_secret_key.get_secret_value()

    identity = await service.authenticate(
        payload.login, payload.password.get_secret_value()
    )
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return await token_response(identity, secret_key, redis)


@router.post("/api/v1/sessions/id", dependencies=[Depends(limit_login_attempts)])
async def login_with_id(
    payload: SystemIdPayload,
    service: Annotated[UserService, Depends(get_user_service)],
    redis: RedisClient,
) -> TokenResponse:
    """Проверяет системный ID и выдаёт пару токенов.

    Raises:
        HTTPException: HTTP 401, если вход по указанному ID недоступен.
    """
    secret_key = settings.jwt_secret_key.get_secret_value()
    identity = await service.authenticate_with_id(str(payload.system_id))
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid system ID"
        )

    return await token_response(identity, secret_key, redis)


@router.post("/api/v1/users/id", status_code=status.HTTP_201_CREATED)
async def signup_with_id(
    service: Annotated[UserService, Depends(get_user_service)],
    redis: RedisClient,
) -> TokenResponse:
    """Создаёт аккаунт без email и пароля.

    Returns:
        Пара токенов и новый системный ID.
    """
    secret_key = settings.jwt_secret_key.get_secret_value()
    identity = await service.signup_with_id()
    return await token_response(identity, secret_key, redis)


@router.post("/api/v1/tokens/refresh")
async def get_refresh_token_route(
    payload: TokenPayload, redis: RedisClient
) -> RefreshAccessTokenResponse:
    """Обменивает действующий одноразовый refresh-токен на новую пару.

    Returns:
        Access-токен и новый refresh-токен.

    Raises:
        HTTPException: HTTP 401 при недействительном refresh или HTTP 503 при ошибке Redis.
    """
    secret_key = settings.jwt_secret_key.get_secret_value()
    try:
        rotated = await rotate_refresh_token(
            redis, payload.refresh_token.get_secret_value()
        )
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token service is unavailable",
        ) from exc

    if rotated is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id, refresh_token = rotated
    return RefreshAccessTokenResponse(
        access_token=create_access_token(user_id, secret_key=secret_key),
        refresh_token=refresh_token,
    )


@router.post(
    "/api/v1/users/employee",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def add_employee(
    payload: AddEmployeePayload,
    service: Annotated[UserService, Depends(get_user_service)],
) -> EmployeeResponse:
    """Создаёт сотрудника по email и паролю с новым системным UUID.

    Returns:
        Внутренний ID и роль сотрудника.

    Raises:
        HTTPException: HTTP 401 при недействительном токене, HTTP 403 при отсутствии
            роли администратора или HTTP 409, если email уже занят.
    """
    role = "marshal" if payload.role == "marshall" else payload.role
    try:
        identity = await service.add_employee(
            login=payload.login, password=payload.password.get_secret_value(), role=role
        )
    except LoginAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login already exists",
        ) from exc

    return EmployeeResponse(id=identity.id, role=role)


@router.get("/api/v1/roles", status_code=status.HTTP_200_OK)
async def get_role(
    user_id: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> RoleResponse:
    """Возвращает текущую роль пользователя из БД."""
    role = await service.get_role_name(user_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return RoleResponse.model_validate({"role": role})

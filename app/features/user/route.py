from math import ceil
from time import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from limits import RateLimitItemPerMinute
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.consts.exceptions import (
    ClassicCredentialsAlreadySetError,
    LoginAlreadyExistsError,
)
from app.core.config import settings
from app.core.jwt_tokens import (
    create_access_token,
    issue_refresh_token,
    rotate_refresh_token,
)
from app.db.redis import get_redis
from app.db.session import get_session
from app.repositories.user_repository import UserIdentity, UserRepository
from app.services.user_service import UserService

from .schemas import (
    LoginPayload,
    RefreshAccessTokenResponse,
    SignupPayload,
    SystemIdPayload,
    TokenResponse,
    TokenPayload,
)

router = APIRouter(tags=["user"])
login_limit = RateLimitItemPerMinute(5)
login_limiter = MovingWindowRateLimiter(MemoryStorage())
RedisClient = Annotated[Redis, Depends(get_redis)]


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repository)


async def token_response(
    identity: UserIdentity, secret_key: str, redis: Redis
) -> TokenResponse:
    access_token = create_access_token(identity.id, secret_key=secret_key)
    try:
        refresh_token = await issue_refresh_token(redis, identity.id)
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
    secret_key = settings.jwt_secret_key.get_secret_value()

    try:
        identity = await service.signup(
            payload.login, payload.password.get_secret_value(), str(payload.system_id)
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
    """Log in with an email and password."""
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
    secret_key = settings.jwt_secret_key.get_secret_value()
    identity = await service.signup_with_id()
    return await token_response(identity, secret_key, redis)


@router.post("/api/v1/tokens/refresh")
async def get_refresh_token(
    payload: TokenPayload, redis: RedisClient
) -> RefreshAccessTokenResponse:
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

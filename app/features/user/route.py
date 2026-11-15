from math import ceil
from time import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from limits import RateLimitItemPerMinute
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.jwt_tokens import create_access_token
from app.db.session import get_session
from app.repositories.user_repository import UserRepository
from app.services.user_service import LoginAlreadyExistsError, UserService

from .schemas import LoginPayload, SignupPayload, TokenResponse

router = APIRouter(tags=["user"])
login_limit = RateLimitItemPerMinute(5)
login_limiter = MovingWindowRateLimiter(MemoryStorage())


def get_user_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repository)


@router.post("/api/v1/users", status_code=status.HTTP_201_CREATED)
async def signup_classic(
    payload: SignupPayload,
    service: Annotated[UserService, Depends(get_user_service)],
) -> TokenResponse:
    secret_key = settings.jwt_secret_key
    if secret_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration is unavailable",
        )

    try:
        identity = await service.signup(payload.login, payload.password.get_secret_value())
    except LoginAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login already exists",
        ) from exc

    return TokenResponse(
        jwt_token=create_access_token(identity.id, secret_key=secret_key.get_secret_value()),
        system_id=identity.system_id,
    )


async def limit_login_attempts(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    if not login_limiter.hit(login_limit, client_ip):
        reset_time, _ = login_limiter.get_window_stats(login_limit, client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts",
            headers={"Retry-After": str(max(1, ceil(reset_time - time())))},
        )


@router.post("/api/v1/sessions", dependencies=[Depends(limit_login_attempts)])
async def login_classic(
    payload: LoginPayload,
    service: Annotated[UserService, Depends(get_user_service)],
) -> TokenResponse:
    """Log in with an email and password."""
    secret_key = settings.jwt_secret_key
    if secret_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login is unavailable",
        )

    identity = await service.authenticate(payload.login, payload.password.get_secret_value())
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(
        jwt_token=create_access_token(identity.id, secret_key=secret_key.get_secret_value()),
        system_id=identity.system_id,
    )

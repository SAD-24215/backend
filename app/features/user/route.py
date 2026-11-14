from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.jwt_tokens import create_access_token
from app.db.session import get_session
from app.repositories.user_repository import UserRepository
from app.services.user_service import LoginAlreadyExistsError, UserService

from .schemas import LoginPayload, SignupPayload, TokenResponse

router = APIRouter(tags=["user"])


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
        user_id = await service.signup(payload.login, payload.password.get_secret_value())
    except LoginAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login already exists",
        ) from exc

    return TokenResponse(
        jwt_token=create_access_token(user_id, secret_key=secret_key.get_secret_value())
    )


@router.post("/api/v1/sessions")
async def login_classic(payload: LoginPayload) -> TokenResponse:
    """Logging in with login and password"""
    return payload

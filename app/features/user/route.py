from fastapi import APIRouter
from .schemas import LoginPayload, TokenResponse

router = APIRouter(tags=["user"])


@router.post("/api/v1/users")
async def signup_classic(payload: LoginPayload) -> LoginPayload:
    """Signing up with login and password"""
    return payload


@router.post("/api/v1/sessions")
async def login_classic(payload: LoginPayload) -> TokenResponse:
    """Logging in with login and password"""
    return payload

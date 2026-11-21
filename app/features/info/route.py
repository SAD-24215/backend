from typing import Annotated

from fastapi import APIRouter, Depends, status
from redis import Redis

from app.features.info.schemas import CartingResponse

router = APIRouter(tags=["info"])


@router.get("/api/v1/info", status_code=status.HTTP_200_OK)
async def get_info() -> CartingResponse:
    return CartingResponse()


@router.put("/api/v1/info", status_code=status.HTTP_200_OK)
async def update_info():
    pass

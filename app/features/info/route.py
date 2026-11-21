from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.consts.dto import CartCenterInfo
from app.core.config import settings
from app.db.session import get_session
from app.repositories.info_repository import InfoRepository
from app.services.info_service import InfoService

from .schemas import CartingPayload, CartingResponse, CartModel

router = APIRouter(tags=["info"])


def get_info_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InfoRepository:
    return InfoRepository(session)


def get_info_service(
    repository: Annotated[InfoRepository, Depends(get_info_repository)],
) -> InfoService:
    return InfoService(repository)


def _info_response(info: CartCenterInfo | None) -> CartingResponse:
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Carting center data not found"
        )

    photo_url = f"http://{settings.app_host}:{settings.app_port}/images/test_image.jpg"
    return CartingResponse(
        address=info.address,
        rules=info.rules,
        price_list=[
            CartModel(
                name="Карт",
                description="Описание появится позже",
                photo_path=photo_url,
                price=0,
            )
        ],
    )


@router.get("/api/v1/info", status_code=status.HTTP_200_OK)
async def get_info(service: Annotated[InfoService, Depends(get_info_service)]) -> CartingResponse:
    return _info_response(await service.get_info())


@router.put("/api/v1/info", status_code=status.HTTP_200_OK)
async def update_info(
    payload: CartingPayload, service: Annotated[InfoService, Depends(get_info_service)]
) -> CartingResponse:
    info = await service.update_info(address=payload.address, rules=payload.rules)
    return _info_response(info)

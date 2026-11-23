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


async def _info_response(
    info: CartCenterInfo | None, service: InfoService
) -> CartingResponse:
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Carting center data not found"
        )

    photo_url = f"http://{settings.app_host}:{settings.app_port}/images/test_image.jpg"
    cart_models = await service.get_cart_models()
    return CartingResponse(
        address=info.address,
        rules=info.rules,
        price_list=[
            CartModel(
                name=cart_model.name,
                description=cart_model.description,
                photo_path=photo_url,
                price=cart_model.price,
                cart_count=cart_model.cart_count,
            )
            for cart_model in cart_models
        ],
    )


@router.get("/api/v1/info", status_code=status.HTTP_200_OK)
async def get_info(service: Annotated[InfoService, Depends(get_info_service)]) -> CartingResponse:
    return await _info_response(await service.get_info(), service)


@router.put("/api/v1/info", status_code=status.HTTP_200_OK)
async def update_info(
    payload: CartingPayload, service: Annotated[InfoService, Depends(get_info_service)]
) -> CartingResponse:
    info = await service.update_info(address=payload.address, rules=payload.rules)
    return await _info_response(info, service)

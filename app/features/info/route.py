from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.consts.dto import CartCenterInfo
from app.consts.exceptions import (
    CartInUseError,
    CartModelInUseError,
    CartModelNotFoundError,
)
from app.core.config import settings
from app.db.session import get_session
from app.repositories.cart_repository import CartRepository
from app.repositories.info_repository import InfoRepository
from app.services.cart_service import CartService
from app.services.info_service import InfoService

from .schemas import (
    AddCartModelPayload,
    AddCartPayload,
    CartingPayload,
    CartingResponse,
    CartModel,
)

router = APIRouter(tags=["info"])


def get_info_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InfoRepository:
    return InfoRepository(session)


def get_info_service(
    repository: Annotated[InfoRepository, Depends(get_info_repository)],
) -> InfoService:
    return InfoService(repository)


def get_cart_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CartRepository:
    return CartRepository(session)


def get_cart_service(
    repository: Annotated[CartRepository, Depends(get_cart_repository)],
) -> CartService:
    return CartService(repository)


async def _info_response(
    info: CartCenterInfo | None, service: InfoService
) -> CartingResponse:
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carting center data not found",
        )

    photo_url = f"http://{settings.app_host}:{settings.app_port}/images/test_image.jpg"
    cart_models = await service.get_cart_models()
    return CartingResponse(
        address=info.address,
        rules=info.rules,
        price_list=[
            CartModel(
                cart_model_id=cart_model.cart_model_id,
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
async def get_info(
    service: Annotated[InfoService, Depends(get_info_service)],
) -> CartingResponse:
    return await _info_response(await service.get_info(), service)


@router.put("/api/v1/info", status_code=status.HTTP_200_OK)
async def update_info(
    payload: CartingPayload, service: Annotated[InfoService, Depends(get_info_service)]
) -> CartingResponse:
    info = await service.update_info(address=payload.address, rules=payload.rules)
    return await _info_response(info, service)


@router.post("/api/v1/carts", status_code=status.HTTP_201_CREATED)
async def add_cart(
    payload: AddCartPayload,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[CartService, Depends(get_cart_service)],
    info_service: Annotated[InfoService, Depends(get_info_service)],
) -> CartingResponse:
    """Добавляет карт и возвращает обновлённую информацию о центре."""
    try:
        async with session.begin():
            cart_id = await service.add_cart(
                cart_model_id=payload.cart_model_id, is_available=payload.is_available
            )
            info = await _info_response(await info_service.get_info(), info_service)
    except CartModelNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cart model not found"
        ) from exc

    response.headers["Location"] = f"/api/v1/carts?cart_id={cart_id}"
    return info


@router.delete(
    "/api/v1/carts", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_cart(
    cart_id: Annotated[int, Query(gt=0, le=2_147_483_647)],
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[CartService, Depends(get_cart_service)],
) -> None:
    """Удаляет карт по ID."""
    try:
        async with session.begin():
            if not await service.delete_cart(cart_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found"
                )
    except CartInUseError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Cart is linked to a run"
        ) from exc


@router.post("/api/v1/cart_models", status_code=status.HTTP_201_CREATED)
async def add_cart_model(
    payload: AddCartModelPayload,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[CartService, Depends(get_cart_service)],
    info_service: Annotated[InfoService, Depends(get_info_service)],
) -> CartingResponse:
    """Добавляет модель карта и возвращает обновлённый прайс-лист."""
    async with session.begin():
        cart_model_id = await service.add_cart_model(
            name=payload.name, description=payload.description, price=payload.price
        )
        info = await _info_response(await info_service.get_info(), info_service)

    response.headers["Location"] = f"/api/v1/cart_models?cart_model_id={cart_model_id}"
    return info


@router.delete(
    "/api/v1/cart_models", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_cart_model(
    cart_model_id: Annotated[int, Query(gt=0, le=2_147_483_647)],
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[CartService, Depends(get_cart_service)],
) -> None:
    """Удаляет модель карты по ID."""
    try:
        async with session.begin():
            if not await service.delete_cart_model(cart_model_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Cart model not found"
                )
    except CartModelInUseError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Cart model is linked to carts"
        ) from exc

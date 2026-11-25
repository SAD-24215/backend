"""Данные картинг-центра, управление картами и их моделями."""

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
from app.features.user.route import require_admin
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
    UpdateCartModelPayload,
    UpdateCartPayload,
)

router = APIRouter(tags=["info"])


def get_info_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InfoRepository:
    """Создаёт репозиторий данных центра с сессией текущего запроса."""
    return InfoRepository(session)


def get_info_service(
    repository: Annotated[InfoRepository, Depends(get_info_repository)],
) -> InfoService:
    """Создаёт сервис картинг-центра для текущего запроса."""
    return InfoService(repository)


def get_cart_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CartRepository:
    """Создаёт репозиторий картов с сессией текущего запроса."""
    return CartRepository(session)


def get_cart_service(
    repository: Annotated[CartRepository, Depends(get_cart_repository)],
) -> CartService:
    """Создаёт сервис картов для текущего запроса."""
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
    """Возвращает данные картинг-центра.

    Args:
        service: Сервис чтения данных центра и прайс-листа.

    Returns:
        Адрес, правила и прайс-лист моделей картов.

    Raises:
        HTTPException: HTTP 404, если записи о центре нет.
    """
    return await _info_response(await service.get_info(), service)


@router.put("/api/v1/info", status_code=status.HTTP_200_OK)
async def update_info(
    payload: CartingPayload, service: Annotated[InfoService, Depends(get_info_service)]
) -> CartingResponse:
    """Обновляет адрес и правила центра.

    Args:
        payload: Новые адрес и правила.
        service: Сервис обновления данных центра.

    Returns:
        Обновлённые данные центра и текущий прайс-лист.

    Raises:
        HTTPException: HTTP 404, если записи о центре нет.
    """
    info = await service.update_info(address=payload.address, rules=payload.rules)
    return await _info_response(info, service)


@router.post(
    "/api/v1/carts",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def add_cart(
    payload: AddCartPayload,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[CartService, Depends(get_cart_service)],
    info_service: Annotated[InfoService, Depends(get_info_service)],
) -> CartingResponse:
    """Добавляет карт выбранной модели.

    Args:
        payload: Идентификатор модели и доступность нового карта.
        response: Ответ для установки заголовка Location с ID карта.
        session: Сессия для транзакции запроса.
        service: Сервис создания карта.
        info_service: Сервис формирования обновлённого прайс-листа.

    Returns:
        Данные центра и прайс-лист с новым количеством картов.

    Raises:
        HTTPException: HTTP 404, если модель или запись о центре отсутствует.
    """
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
    "/api/v1/carts",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(require_admin)],
)
async def delete_cart(
    cart_id: Annotated[int, Query(gt=0, le=2_147_483_647)],
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[CartService, Depends(get_cart_service)],
) -> None:
    """Удаляет карт по ID и возвращает HTTP 204.

    Args:
        cart_id: Идентификатор удаляемого карта.
        session: Сессия для транзакции запроса.
        service: Сервис удаления карта.

    Raises:
        HTTPException: HTTP 404, если карта нет, или HTTP 409,
            если он связан с заездом.
    """
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


@router.put(
    "/api/v1/carts",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin)],
)
async def update_cart(
    payload: UpdateCartPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[CartService, Depends(get_cart_service)],
    info_service: Annotated[InfoService, Depends(get_info_service)],
) -> CartingResponse:
    """Обновляет модель и доступность карта.

    Args:
        payload: ID карта, ID модели и новое значение доступности.
        session: Сессия для транзакции запроса.
        service: Сервис обновления карта.
        info_service: Сервис формирования обновлённого прайс-листа.

    Returns:
        Данные центра и прайс-лист после обновления.

    Raises:
        HTTPException: HTTP 404, если карт, модель или запись о центре
            отсутствуют.
    """
    try:
        async with session.begin():
            updated = await service.update_cart(
                payload.id,
                cart_model_id=payload.cart_model_id,
                is_available=payload.is_available,
            )
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found"
                )
            return await _info_response(await info_service.get_info(), info_service)
    except CartModelNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cart model not found"
        ) from exc


@router.post(
    "/api/v1/cart_models",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def add_cart_model(
    payload: AddCartModelPayload,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[CartService, Depends(get_cart_service)],
    info_service: Annotated[InfoService, Depends(get_info_service)],
) -> CartingResponse:
    """Добавляет модель карта.

    Args:
        payload: Название, описание и цена модели.
        response: Ответ для установки заголовка Location с ID модели.
        session: Сессия для транзакции запроса.
        service: Сервис создания модели.
        info_service: Сервис формирования обновлённого прайс-листа.

    Returns:
        Данные центра и прайс-лист с новой моделью.

    Raises:
        HTTPException: HTTP 404, если записи о центре нет.
    """
    async with session.begin():
        cart_model_id = await service.add_cart_model(
            name=payload.name, description=payload.description, price=payload.price
        )
        info = await _info_response(await info_service.get_info(), info_service)

    response.headers["Location"] = f"/api/v1/cart_models?cart_model_id={cart_model_id}"
    return info


@router.delete(
    "/api/v1/cart_models",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(require_admin)],
)
async def delete_cart_model(
    cart_model_id: Annotated[int, Query(gt=0, le=2_147_483_647)],
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[CartService, Depends(get_cart_service)],
) -> None:
    """Удаляет модель карта и возвращает HTTP 204.

    Args:
        cart_model_id: Идентификатор удаляемой модели.
        session: Сессия для транзакции запроса.
        service: Сервис удаления модели.

    Raises:
        HTTPException: HTTP 404, если модели нет, или HTTP 409,
            если к ней привязаны карты.
    """
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


@router.put(
    "/api/v1/cart_models",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin)],
)
async def update_cart_model(
    payload: UpdateCartModelPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[CartService, Depends(get_cart_service)],
    info_service: Annotated[InfoService, Depends(get_info_service)],
) -> CartingResponse:
    """Обновляет модель карта в прайс-листе.

    Args:
        payload: ID модели и её новые название, описание и цена.
        session: Сессия для транзакции запроса.
        service: Сервис обновления модели.
        info_service: Сервис формирования обновлённого прайс-листа.

    Returns:
        Данные центра и прайс-лист с обновлённой моделью.

    Raises:
        HTTPException: HTTP 404, если модель или запись о центре отсутствует.
    """
    async with session.begin():
        updated = await service.update_cart_model(
            payload.id,
            name=payload.name,
            description=payload.description,
            price=payload.price,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cart model not found"
            )
        return await _info_response(await info_service.get_info(), info_service)

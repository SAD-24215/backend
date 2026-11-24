"""Создание, обновление и удаление картов и их моделей."""

from sqlalchemy import delete, insert, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.consts.exceptions import (
    CartInUseError,
    CartModelInUseError,
    CartModelNotFoundError,
)
from app.db.models import Cart, CartModel


class CartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_cart(self, *, cart_model_id: int, is_available: bool) -> int:
        """Добавляет карт и возвращает его ID в текущей транзакции."""
        statement = (
            insert(Cart)
            .values(cart_model_id=cart_model_id, is_available=is_available)
            .returning(Cart.id)
        )
        try:
            result = await self.session.execute(statement)
        except IntegrityError as exc:
            if getattr(exc.orig, "sqlstate", None) == "23503":
                raise CartModelNotFoundError from exc
            raise
        return result.scalar_one()

    async def delete_cart(self, cart_id: int) -> bool:
        """Удаляет карт без связанных заездов, если он существует."""
        statement = delete(Cart).where(Cart.id == cart_id).returning(Cart.id)
        try:
            result = await self.session.execute(statement)
        except IntegrityError as exc:
            if getattr(exc.orig, "sqlstate", None) == "23503":
                raise CartInUseError from exc
            raise
        return result.scalar_one_or_none() is not None

    async def update_cart(
        self, cart_id: int, *, cart_model_id: int, is_available: bool
    ) -> bool:
        """Обновляет модель и доступность карта в текущей транзакции."""
        statement = (
            update(Cart)
            .where(Cart.id == cart_id)
            .values(cart_model_id=cart_model_id, is_available=is_available)
            .returning(Cart.id)
        )
        try:
            result = await self.session.execute(statement)
        except IntegrityError as exc:
            if getattr(exc.orig, "sqlstate", None) == "23503":
                raise CartModelNotFoundError from exc
            raise
        return result.scalar_one_or_none() is not None

    async def add_cart_model(self, *, name: str, description: str, price: int) -> int:
        """Добавляет модель карта и возвращает её ID в текущей транзакции."""
        statement = (
            insert(CartModel)
            .values(model=name, description=description, price=price)
            .returning(CartModel.id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def delete_cart_model(self, cart_model_id: int) -> bool:
        """Удаляет модель без связанных картов, если она существует."""
        statement = (
            delete(CartModel).where(CartModel.id == cart_model_id).returning(CartModel.id)
        )
        try:
            result = await self.session.execute(statement)
        except IntegrityError as exc:
            if getattr(exc.orig, "sqlstate", None) == "23503":
                raise CartModelInUseError from exc
            raise
        return result.scalar_one_or_none() is not None

    async def update_cart_model(
        self, cart_model_id: int, *, name: str, description: str, price: int
    ) -> bool:
        """Обновляет название, описание и цену модели карта."""
        statement = (
            update(CartModel)
            .where(CartModel.id == cart_model_id)
            .values(model=name, description=description, price=price)
            .returning(CartModel.id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None

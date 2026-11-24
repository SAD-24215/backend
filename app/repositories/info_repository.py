"""Чтение и обновление данных картинг-центра."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.consts.dto import CartCenterInfo, CartModelInfo
from app.db.models import Cart, CartCenterData, CartModel


class InfoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_info(self) -> CartCenterInfo | None:
        """Читает первую запись с данными центра по возрастанию ID."""
        statement = (
            select(CartCenterData.address, CartCenterData.rules)
            .order_by(CartCenterData.id)
            .limit(1)
        )
        result = await self.session.execute(statement)
        row = result.one_or_none()
        if row is None:
            return None
        return CartCenterInfo(address=row.address, rules=row.rules)

    async def get_cart_models(self) -> list[CartModelInfo]:
        """Читает модели по возрастанию ID и считает карты каждой модели."""
        statement = (
            select(
                CartModel.id.label("cart_model_id"),
                CartModel.model,
                CartModel.description,
                CartModel.price,
                func.count(Cart.id).label("cart_count"),
            )
            .outerjoin(Cart, Cart.cart_model_id == CartModel.id)
            .group_by(CartModel.id, CartModel.model, CartModel.description, CartModel.price)
            .order_by(CartModel.id)
        )
        result = await self.session.execute(statement)
        return [
            CartModelInfo(
                cart_model_id=row.cart_model_id,
                name=row.model,
                description=row.description,
                price=row.price,
                cart_count=row.cart_count,
            )
            for row in result
        ]

    async def update_info(self, *, address: str, rules: str) -> CartCenterInfo | None:
        """Сохраняет адрес и правила и возвращает обновлённые данные."""
        center_id = select(CartCenterData.id).order_by(CartCenterData.id).limit(1)
        statement = (
            update(CartCenterData)
            .where(CartCenterData.id == center_id.scalar_subquery())
            .values(address=address, rules=rules)
            .returning(CartCenterData.address, CartCenterData.rules)
        )
        async with self.session.begin():
            result = await self.session.execute(statement)
            row = result.one_or_none()

        if row is None:
            return None
        return CartCenterInfo(address=row.address, rules=row.rules)

"""Чтение и обновление данных картинг-центра."""

from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.consts.dto import CartCenterInfo
from app.db.models import CartCenterData


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

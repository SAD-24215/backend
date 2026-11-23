"""Работа с данными картинг-центра."""

from app.consts.dto import CartCenterInfo, CartModelInfo
from app.repositories.info_repository import InfoRepository


class InfoService:
    def __init__(self, repository: InfoRepository) -> None:
        self.repository = repository

    async def get_info(self) -> CartCenterInfo | None:
        return await self.repository.get_info()

    async def get_cart_models(self) -> list[CartModelInfo]:
        """Возвращает модели картов для прайс-листа."""
        return await self.repository.get_cart_models()

    async def update_info(self, *, address: str, rules: str) -> CartCenterInfo | None:
        return await self.repository.update_info(address=address, rules=rules)

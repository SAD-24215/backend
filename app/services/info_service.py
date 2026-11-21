"""Работа с данными картинг-центра."""

from app.consts.dto import CartCenterInfo
from app.repositories.info_repository import InfoRepository


class InfoService:
    def __init__(self, repository: InfoRepository) -> None:
        self.repository = repository

    async def get_info(self) -> CartCenterInfo | None:
        return await self.repository.get_info()

    async def update_info(self, *, address: str, rules: str) -> CartCenterInfo | None:
        return await self.repository.update_info(address=address, rules=rules)

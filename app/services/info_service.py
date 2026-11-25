"""Работа с данными картинг-центра."""

from app.consts.dto import CartCenterInfo, CartModelInfo
from app.repositories.info_repository import InfoRepository


class InfoService:
    """Получает и обновляет данные картинг-центра.

    Args:
        repository: Репозиторий данных центра и прайс-листа.
    """

    def __init__(self, repository: InfoRepository) -> None:
        self.repository = repository

    async def get_info(self) -> CartCenterInfo | None:
        """Получает данные картинг-центра.

        Returns:
            Адрес и правила или None, если записи о центре нет.
        """
        return await self.repository.get_info()

    async def get_cart_models(self) -> list[CartModelInfo]:
        """Получает модели картов для прайс-листа.

        Returns:
            Список моделей с ценой, описанием и общим числом картов каждой модели.
        """
        return await self.repository.get_cart_models()

    async def update_info(self, *, address: str, rules: str) -> CartCenterInfo | None:
        """Обновляет данные картинг-центра.

        Args:
            address: Новый адрес центра.
            rules: Новые правила центра.

        Returns:
            Сохранённые данные или None, если записи о центре нет.
        """
        return await self.repository.update_info(address=address, rules=rules)

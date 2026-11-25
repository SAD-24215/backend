"""Операции с картами и их моделями."""

from app.repositories.cart_repository import CartRepository


class CartService:
    """Создаёт, обновляет и удаляет карты и их модели.

    Args:
        repository: Репозиторий картов и моделей.
    """

    def __init__(self, repository: CartRepository) -> None:
        self.repository = repository

    async def add_cart(self, *, cart_model_id: int, is_available: bool) -> int:
        """Создаёт карт выбранной модели.

        Args:
            cart_model_id: Идентификатор модели.
            is_available: Доступность нового карта.

        Returns:
            Идентификатор созданного карта.

        Raises:
            CartModelNotFoundError: Выбранная модель отсутствует.
        """
        return await self.repository.add_cart(
            cart_model_id=cart_model_id, is_available=is_available
        )

    async def delete_cart(self, cart_id: int) -> bool:
        """Удаляет карт по ID.

        Args:
            cart_id: Идентификатор удаляемого карта.

        Returns:
            True при удалении, False при отсутствии карта.

        Raises:
            CartInUseError: Карт связан с заездом.
        """
        return await self.repository.delete_cart(cart_id)

    async def update_cart(
        self, cart_id: int, *, cart_model_id: int, is_available: bool
    ) -> bool:
        """Обновляет модель и доступность карта.

        Args:
            cart_id: Идентификатор обновляемого карта.
            cart_model_id: Идентификатор назначаемой модели.
            is_available: Новая доступность.

        Returns:
            True при обновлении, False при отсутствии карта.

        Raises:
            CartModelNotFoundError: Назначаемая модель отсутствует.
        """
        return await self.repository.update_cart(
            cart_id, cart_model_id=cart_model_id, is_available=is_available
        )

    async def add_cart_model(self, *, name: str, description: str, price: int) -> int:
        """Создаёт модель карта.

        Args:
            name: Название модели.
            description: Описание модели.
            price: Цена модели.

        Returns:
            Идентификатор созданной модели.
        """
        return await self.repository.add_cart_model(
            name=name, description=description, price=price
        )

    async def delete_cart_model(self, cart_model_id: int) -> bool:
        """Удаляет модель по ID.

        Args:
            cart_model_id: Идентификатор удаляемой модели.

        Returns:
            True при удалении, False при отсутствии модели.

        Raises:
            CartModelInUseError: К модели привязаны карты.
        """
        return await self.repository.delete_cart_model(cart_model_id)

    async def update_cart_model(
        self, cart_model_id: int, *, name: str, description: str, price: int
    ) -> bool:
        """Обновляет модель карта.

        Args:
            cart_model_id: Идентификатор обновляемой модели.
            name: Новое название.
            description: Новое описание.
            price: Новая цена.

        Returns:
            True при обновлении, False при отсутствии модели.
        """
        return await self.repository.update_cart_model(
            cart_model_id, name=name, description=description, price=price
        )

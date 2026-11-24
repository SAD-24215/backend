"""Операции с картами и их моделями."""

from app.repositories.cart_repository import CartRepository


class CartService:
    def __init__(self, repository: CartRepository) -> None:
        self.repository = repository

    async def add_cart(self, *, cart_model_id: int, is_available: bool) -> int:
        """Добавляет карт выбранной модели и возвращает его ID."""
        return await self.repository.add_cart(
            cart_model_id=cart_model_id, is_available=is_available
        )

    async def delete_cart(self, cart_id: int) -> bool:
        """Удаляет карт по ID."""
        return await self.repository.delete_cart(cart_id)

    async def add_cart_model(self, *, name: str, description: str, price: int) -> int:
        """Добавляет модель карты и возвращает её ID."""
        return await self.repository.add_cart_model(
            name=name, description=description, price=price
        )

    async def delete_cart_model(self, cart_model_id: int) -> bool:
        """Удаляет модель карты по ID."""
        return await self.repository.delete_cart_model(cart_model_id)

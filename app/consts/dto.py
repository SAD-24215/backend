from dataclasses import dataclass


@dataclass(frozen=True)
class UserIdentity:
    """Идентификаторы пользователя, которые нужны после регистрации или входа.

    Attributes:
        id: Внутренний ID пользователя в базе данных.
        system_id: Системный UUID аккаунта.
    """

    id: int
    system_id: str


@dataclass(frozen=True)
class CartCenterInfo:
    address: str
    rules: str


@dataclass(frozen=True)
class CartModelInfo:
    """Данные модели карты и количество её экземпляров."""

    name: str
    description: str
    price: int
    cart_count: int

"""Схемы API картинг-центра, картов и их моделей."""

from pydantic import BaseModel, Field


class CartModel(BaseModel):
    """Модель карта в прайс-листе.

    Attributes:
        cart_model_id: Идентификатор модели в базе данных.
        name: Название модели.
        description: Описание модели.
        photo_path: URL изображения.
        price: Цена модели.
        cart_count: Общее число картов модели, включая недоступные.
    """

    cart_model_id: int
    name: str
    description: str
    photo_path: str
    price: int
    cart_count: int


class CartingData(BaseModel):
    """Данные картинг-центра.

    Attributes:
        address: Адрес центра.
        rules: Правила посещения и заездов.
    """

    address: str = Field(max_length=1000)
    rules: str = Field(max_length=1000)


class CartingResponse(CartingData):
    """Данные центра и актуальный прайс-лист.

    Attributes:
        price_list: Модели картов в порядке возрастания их ID.
    """

    price_list: list[CartModel] = Field(default_factory=list)


class CartingPayload(CartingData):
    """Новые адрес и правила картинг-центра."""

    pass


class AddCartPayload(BaseModel):
    """Данные для создания карта.

    Attributes:
        cart_model_id: Идентификатор существующей модели.
        is_available: Доступность карта. По умолчанию карт доступен.
    """

    cart_model_id: int = Field(gt=0, le=2_147_483_647)
    is_available: bool = True


class UpdateCartPayload(AddCartPayload):
    """Данные для обновления карта.

    Attributes:
        id: Идентификатор обновляемого карта.
        cart_model_id: Идентификатор модели, которую нужно назначить.
        is_available: Новое обязательное значение доступности.
    """

    id: int = Field(gt=0, le=2_147_483_647)
    is_available: bool = Field()


class AddCartModelPayload(BaseModel):
    """Данные для создания модели карта.

    Attributes:
        name: Название модели.
        description: Описание модели.
        price: Неотрицательная цена.
    """

    name: str = Field(min_length=1, max_length=255, pattern=r"^[^\x00]+$")
    description: str = Field(max_length=1000, pattern=r"^[^\x00]*$")
    price: int = Field(ge=0, le=2_147_483_647)


class UpdateCartModelPayload(AddCartModelPayload):
    """Данные для обновления модели карта.

    Attributes:
        id: Идентификатор модели, чьи название, описание и цена обновляются.
    """

    id: int = Field(gt=0, le=2_147_483_647)

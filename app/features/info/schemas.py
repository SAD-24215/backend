from pydantic import BaseModel, Field, SecretStr, field_validator


class CartModel(BaseModel):
    name: str
    photo_path: str
    price: int


class CartingData(BaseModel):
    address: str = ""
    price_list: list[CartModel] = []
    rules: str = ""


class CartingResponse(CartingData):
    pass


class CartingPayload(CartingData):
    pass

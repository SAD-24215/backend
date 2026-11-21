from pydantic import BaseModel, Field


class CartModel(BaseModel):
    name: str
    description: str
    photo_path: str
    price: int


class CartingData(BaseModel):
    address: str = Field(max_length=1000)
    rules: str = Field(max_length=1000)


class CartingResponse(CartingData):
    price_list: list[CartModel] = Field(default_factory=list)


class CartingPayload(CartingData):
    pass

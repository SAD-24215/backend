from pydantic import BaseModel, Field


class CartModel(BaseModel):
    cart_model_id: int
    name: str
    description: str
    photo_path: str
    price: int
    cart_count: int


class CartingData(BaseModel):
    address: str = Field(max_length=1000)
    rules: str = Field(max_length=1000)


class CartingResponse(CartingData):
    price_list: list[CartModel] = Field(default_factory=list)


class CartingPayload(CartingData):
    pass


class AddCartPayload(BaseModel):
    cart_model_id: int = Field(gt=0, le=2_147_483_647)
    is_available: bool = True


class UpdateCartPayload(AddCartPayload):
    id: int = Field(gt=0, le=2_147_483_647)
    is_available: bool = Field()


class AddCartModelPayload(BaseModel):
    name: str = Field(min_length=1, max_length=255, pattern=r"^[^\x00]+$")
    description: str = Field(max_length=1000, pattern=r"^[^\x00]*$")
    price: int = Field(ge=0, le=2_147_483_647)


class UpdateCartModelPayload(AddCartModelPayload):
    id: int = Field(gt=0, le=2_147_483_647)

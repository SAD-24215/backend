from pydantic import BaseModel


class LoginPayload(BaseModel):
    login: str
    password: str


class TokenResponse(BaseModel):
    jwt_token: str

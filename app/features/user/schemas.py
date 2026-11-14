from pydantic import BaseModel, Field, SecretStr


class LoginPayload(BaseModel):
    login: str = Field(min_length=1, max_length=100, pattern=r"^[^\x00]+$")
    password: SecretStr = Field(min_length=1, max_length=1024)


class SignupPayload(BaseModel):
    login: str = Field(min_length=1, max_length=100, pattern=r"^[^\x00]+$")
    password: SecretStr = Field(min_length=1, max_length=1024)


class TokenResponse(BaseModel):
    jwt_token: str

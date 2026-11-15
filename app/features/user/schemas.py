from email_validator import validate_email
from pydantic import BaseModel, Field, SecretStr, field_validator


class LoginPayload(BaseModel):
    login: str = Field(min_length=1, max_length=100, pattern=r"^[^\x00]+$")
    password: SecretStr = Field(min_length=1, max_length=1024)


class SignupPayload(BaseModel):
    login: str = Field(min_length=1, max_length=100, pattern=r"^[^\x00]+$")
    password: SecretStr = Field(min_length=1, max_length=1024)

    @field_validator("login")
    @classmethod
    def validate_login_email(cls, login: str) -> str:
        validate_email(login, check_deliverability=False)
        return login


class TokenResponse(BaseModel):
    jwt_token: str
    system_id: str

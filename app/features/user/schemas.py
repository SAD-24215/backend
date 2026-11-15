from email_validator import validate_email
from pydantic import UUID4, BaseModel, Field, SecretStr, field_validator


class LoginPayload(BaseModel):
    login: str = Field(min_length=1, max_length=100, pattern=r"^[^\x00]+$")
    password: SecretStr = Field(min_length=1, max_length=1024)


class SystemIdPayload(BaseModel):
    system_id: UUID4


class SignupPayload(SystemIdPayload):
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

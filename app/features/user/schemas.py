"""Схемы запросов и ответов API авторизации."""

from typing import Optional

from email_validator import validate_email
from pydantic import UUID4, BaseModel, Field, SecretStr, field_validator


class LoginPayload(BaseModel):
    """Данные для входа по email и паролю.

    Attributes:
        login: Email пользователя.
        password: Пароль пользователя.
    """

    login: str = Field(min_length=1, max_length=100, pattern=r"^[^\x00]+$")
    password: SecretStr = Field(min_length=1, max_length=1024)


class SystemIdPayload(BaseModel):
    """Данные для входа по системному идентификатору.

    Attributes:
        system_id: Системный идентификатор в формате UUIDv4.
    """

    system_id: UUID4


class TokenPayload(BaseModel):
    """Запрос на обновление токенов.

    Attributes:
        refresh_token: Текущий одноразовый refresh-токен.
    """

    refresh_token: SecretStr = Field(min_length=1, max_length=256)


class SignupPayload(SystemIdPayload):
    """Email и пароль для привязки к существующему аккаунту.

    Attributes:
        login: Email для входа.
        password: Пароль для входа.
    """

    login: str = Field(min_length=1, max_length=100, pattern=r"^[^\x00]+$")
    password: SecretStr = Field(min_length=1, max_length=1024)

    @field_validator("login")
    @classmethod
    def validate_login_email(cls, login: str) -> str:
        """Проверяет формат email без DNS-запроса и возвращает исходную строку."""
        validate_email(login, check_deliverability=False)
        return login


class RefreshAccessTokenResponse(BaseModel):
    """Пара токенов после обновления сессии.

    Attributes:
        access_token: Подписанный JWT для запросов к API.
        refresh_token: Одноразовый токен для следующего обновления.
    """

    access_token: str
    refresh_token: str


class TokenResponse(RefreshAccessTokenResponse):
    """Ответ регистрации или входа с парой токенов.

    Attributes:
        system_id: Системный идентификатор пользователя.
    """

    system_id: str

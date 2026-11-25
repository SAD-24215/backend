"""Схемы запросов и ответов API авторизации."""

from typing import Literal

from email_validator import validate_email
from pydantic import UUID4, BaseModel, ConfigDict, Field, SecretStr, field_validator


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


class NewCredentialsPayload(LoginPayload):
    """Email и пароль для записи учётных данных."""

    @field_validator("login")
    @classmethod
    def validate_login_email(cls, login: str) -> str:
        """Проверяет формат email без DNS-запроса.

        Args:
            login: Email из данных для регистрации или создания сотрудника.

        Returns:
            Исходная строка email.

        Raises:
            EmailNotValidError: Некорректный формат адреса.
        """
        validate_email(login, check_deliverability=False)
        return login


class SignupPayload(NewCredentialsPayload):
    """Email и пароль для регистрации или привязки к существующему аккаунту.

    Attributes:
        system_id: Идентификатор существующего аккаунта, если нужно привязать данные.
    """

    system_id: UUID4 | None = None


class AddEmployeePayload(NewCredentialsPayload):
    """Учётные данные нового сотрудника.

    Attributes:
        role: Роль admin или marshal. Вариант marshall принимается как marshal.
    """

    model_config = ConfigDict(extra="forbid")

    role: Literal["admin", "marshal", "marshall"]


class EmployeeResponse(BaseModel):
    """Данные созданного сотрудника.

    Attributes:
        id: Внутренний ID сотрудника.
        role: Роль сотрудника в БД.
    """

    id: int
    role: Literal["admin", "marshal"]


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


class RoleResponse(BaseModel):
    """Ответ с ролью пользователя.

    Attributes:
        role: Текущая роль из БД, admin, marshal или customer.
    """

    role: Literal["admin", "marshal", "customer"]

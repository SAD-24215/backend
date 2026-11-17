"""Регистрация и проверка учётных данных пользователей."""

from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.repositories.user_repository import UserIdentity, UserRepository

password_hasher = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hasher.hash("unused-login-password")


class UserService:
    """Работает с регистрацией, паролями и входом по системному ID.

    Args:
        repository: Репозиторий пользователей.
    """

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def signup(
        self, login: str | None, password: str | None, system_id: str | None
    ) -> UserIdentity | None:
        """Хеширует пароль и привязывает его вместе с email к существующему аккаунту.

        Args:
            login: Email для входа.
            password: Пароль из запроса регистрации.
            system_id: Системный идентификатор аккаунта.

        Returns:
            Идентификаторы пользователя или ``None``, если подходящий аккаунт не найден.

        Raises:
            IntegrityError: Одно или несколько обязательных полей равны ``None``.
        """
        if login is None or password is None or system_id is None:
            raise IntegrityError(
                None, None, ValueError("login, password and system_id are required")
            )

        password_hash = await run_in_threadpool(password_hasher.hash, password)
        return await self.repository.set_classic_credentials(
            system_id=system_id, login=login, password_hash=password_hash
        )

    async def signup_with_id(self) -> UserIdentity:
        """Создаёт аккаунт для входа по UUID без email и пароля.

        Returns:
            Внутренний и системный идентификаторы нового пользователя.
        """
        return await self.repository.create_customer_with_id()

    async def authenticate_with_id(self, system_id: str | None) -> UserIdentity | None:
        """Проверяет, доступен ли вход по указанному системному ID.

        Args:
            system_id: Системный идентификатор из запроса входа.

        Returns:
            Идентификаторы пользователя или ``None``, если вход по этому ID недоступен.
        """
        if system_id is None:
            return None

        return await self.repository.get_by_system_id(system_id)

    async def authenticate(self, email: str | None, password: str | None) -> UserIdentity | None:
        """Ищет пользователя по email и сверяет пароль с сохранённым хешем.

        Args:
            email: Email, указанный при входе.
            password: Пароль, указанный при входе.

        Returns:
            Идентификаторы пользователя или ``None`` при неверных учётных данных.
        """
        if email is None or password is None:
            return None

        user = await self.repository.get_by_email(email)
        stored_hash = user.password_hash if user is not None else None
        password_matches = await run_in_threadpool(
            password_hasher.verify, password, stored_hash or DUMMY_PASSWORD_HASH
        )
        if user is None or not stored_hash or not password_matches:
            return None
        return UserIdentity(id=user.id, system_id=user.system_id)

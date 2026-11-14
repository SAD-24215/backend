from pwdlib import PasswordHash
from starlette.concurrency import run_in_threadpool

from app.consts.exceptions import LoginAlreadyExistsError
from app.repositories.user_repository import UserRepository

password_hasher = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hasher.hash("unused-login-password")


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def signup(self, login: str, password: str) -> int:
        password_hash = await run_in_threadpool(password_hasher.hash, password)
        user_id = await self.repository.create_customer(
            login=login, password_hash=password_hash
        )
        if user_id is None:
            raise LoginAlreadyExistsError
        return user_id

    async def authenticate(self, email: str, password: str) -> int | None:
        user = await self.repository.get_by_email(email)
        stored_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
        password_matches = await run_in_threadpool(
            password_hasher.verify, password, stored_hash
        )
        if user is None or not password_matches:
            return None
        return user.id

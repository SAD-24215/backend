from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.consts.exceptions import ClassicCredentialsAlreadySetError, LoginAlreadyExistsError
from app.db.models import Role, User


@dataclass(frozen=True)
class UserIdentity:
    id: int
    system_id: str


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_customer_with_id(self) -> UserIdentity:
        role_id = select(Role.id).where(Role.name == "customer").scalar_subquery()
        statement = (
            insert(User)
            .values(system_id=str(uuid4()), role_id=role_id, system_id_login_enabled=True)
            .returning(User.id, User.system_id)
        )

        async with self.session.begin():
            result = await self.session.execute(statement)
            row = result.one()

        return UserIdentity(id=row.id, system_id=row.system_id)

    async def get_by_system_id(self, system_id: str) -> UserIdentity | None:
        result = await self.session.execute(
            select(User.id, User.system_id).where(
                User.system_id == system_id, User.system_id_login_enabled.is_(True)
            )
        )
        row = result.one_or_none()
        if row is None:
            return None
        return UserIdentity(id=row.id, system_id=row.system_id)

    async def set_classic_credentials(
        self, *, system_id: str, login: str, password_hash: str
    ) -> UserIdentity | None:
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    select(User)
                    .where(User.system_id == system_id, User.system_id_login_enabled.is_(True))
                    .with_for_update()
                )
                user = result.scalar_one_or_none()
                if user is None:
                    return None
                if user.email is not None or user.password_hash is not None:
                    raise ClassicCredentialsAlreadySetError

                user.name = login
                user.email = login
                user.password_hash = password_hash
                return UserIdentity(id=user.id, system_id=user.system_id)
        except IntegrityError as exc:
            if getattr(exc.orig, "sqlstate", None) == "23505":
                raise LoginAlreadyExistsError from exc
            raise

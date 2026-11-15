from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def create_customer(self, *, login: str, password_hash: str) -> UserIdentity | None:
        role_id = select(Role.id).where(Role.name == "customer").scalar_subquery()
        statement = (
            insert(User)
            .values(
                name=login,
                email=login,
                system_id=str(uuid4()),
                password_hash=password_hash,
                role_id=role_id,
            )
            .on_conflict_do_nothing(index_elements=[User.email])
            .returning(User.id, User.system_id)
        )

        async with self.session.begin():
            result = await self.session.execute(statement)
            row = result.one_or_none()

        if row is None:
            return None
        return UserIdentity(id=row.id, system_id=row.system_id)

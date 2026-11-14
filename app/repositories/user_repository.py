from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Role, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_customer(self, *, login: str, password_hash: str) -> int | None:
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
            .returning(User.id)
        )

        async with self.session.begin():
            result = await self.session.execute(statement)
            return result.scalar_one_or_none()

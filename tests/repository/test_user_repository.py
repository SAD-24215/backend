from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.consts.dto import UserIdentity
from app.consts.exceptions import LoginAlreadyExistsError
from app.db.models import User
from app.repositories.user_repository import UserRepository


pytestmark = pytest.mark.asyncio
PASSWORD_HASH = "test-password-hash"


@pytest.fixture
def repository(db_session: AsyncSession) -> UserRepository:
    return UserRepository(db_session)


@pytest_asyncio.fixture(loop_scope="function")
async def account(repository: UserRepository) -> UserIdentity:
    return await repository.create_customer_with_id()


async def test_get_by_email_returns_none_for_null(
    repository: UserRepository, account: UserIdentity
) -> None:
    assert await repository.get_by_email(None) is None


async def test_get_by_email_returns_none_for_unknown_email(repository: UserRepository) -> None:
    assert await repository.get_by_email(f"{uuid4().hex}@example.com") is None


async def test_get_by_email_returns_user_for_known_email(
    repository: UserRepository, account: UserIdentity
) -> None:
    local_part = uuid4().hex
    email = f"{local_part}@EXAMPLE.COM"
    assert await repository.set_classic_credentials(
        system_id=account.system_id, login=email, password_hash=PASSWORD_HASH
    ) == account

    result = await repository.get_by_email(email)

    assert isinstance(result, User)
    assert result.id == account.id
    assert result.email == f"{local_part}@example.com"


async def test_create_customer_rejects_equivalent_email(repository: UserRepository) -> None:
    local_part = uuid4().hex
    email = f"{local_part}@example.com"
    identity = await repository.create_customer(
        login=f"{local_part}@EXAMPLE.COM", password_hash=PASSWORD_HASH
    )

    with pytest.raises(LoginAlreadyExistsError):
        await repository.create_customer(login=email, password_hash=PASSWORD_HASH)

    result = await repository.get_by_email(email)
    assert isinstance(result, User)
    assert result.id == identity.id
    assert result.email == email


@pytest.mark.parametrize("case", ["all-null", "unknown-system-id", "invalid-login"])
async def test_set_classic_credentials_returns_none_for_invalid_input(
    repository: UserRepository, db_session: AsyncSession, account: UserIdentity, case: str
) -> None:
    valid_email = f"{uuid4().hex}@example.com"
    system_id, login, password_hash = {
        "all-null": (None, None, None),
        "unknown-system-id": (str(uuid4()), valid_email, PASSWORD_HASH),
        "invalid-login": (account.system_id, "not-an-email", PASSWORD_HASH),
    }[case]

    result = await repository.set_classic_credentials(
        system_id=system_id, login=login, password_hash=password_hash
    )

    assert result is None
    stored_account = await db_session.get(User, account.id)
    assert stored_account is not None
    assert stored_account.email is None
    assert stored_account.password_hash is None

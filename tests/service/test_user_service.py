from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.consts.dto import UserIdentity
from app.consts.exceptions import LoginAlreadyExistsError
from app.db.models import User
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


pytestmark = pytest.mark.asyncio
PASSWORD = "service-test-password"
WRONG_PASSWORD = "wrong-test-password"


@pytest.fixture
def user_service(db_session: AsyncSession) -> UserService:
    return UserService(UserRepository(db_session))


@pytest.fixture
def email() -> str:
    return f"{uuid4().hex}@example.com"


@pytest_asyncio.fixture(loop_scope="function")
async def registered_account(user_service: UserService, email: str) -> UserIdentity:
    account = await user_service.signup_with_id()
    assert await user_service.signup(email, PASSWORD, account.system_id) == account
    return account


@pytest.mark.parametrize(
    "missing_fields",
    [
        ("login", "password", "system_id"),
        ("login", "password"),
        ("login", "system_id"),
        ("password", "system_id"),
        ("login",),
        ("password",),
        ("system_id",),
    ],
    ids=lambda fields: "+".join(fields),
)
async def test_signup_rejects_any_null_field(
    user_service: UserService, email: str, missing_fields: tuple[str, ...]
) -> None:
    account = await user_service.signup_with_id()
    login = None if "login" in missing_fields else email
    password = None if "password" in missing_fields else PASSWORD
    system_id = None if "system_id" in missing_fields else account.system_id

    with pytest.raises(IntegrityError):
        await user_service.signup(login, password, system_id)

    assert await user_service.signup(email, PASSWORD, account.system_id) == account


async def test_signup_links_credentials_to_existing_account(
    user_service: UserService, db_session: AsyncSession, email: str
) -> None:
    account = await user_service.signup_with_id()

    result = await user_service.signup(email, PASSWORD, account.system_id)

    assert isinstance(result, UserIdentity)
    assert result == account
    saved_user = await db_session.get(User, account.id)
    assert saved_user is not None
    assert saved_user.email == email
    assert saved_user.password_hash and saved_user.password_hash != PASSWORD


@pytest.mark.parametrize(
    "password", [PASSWORD, WRONG_PASSWORD], ids=["same-password", "other-password"]
)
async def test_signup_rejects_login_already_used_by_another_account(
    user_service: UserService, registered_account: UserIdentity, email: str, password: str
) -> None:
    other_account = await user_service.signup_with_id()

    with pytest.raises(LoginAlreadyExistsError):
        await user_service.signup(email, password, other_account.system_id)

    assert await user_service.authenticate(email, PASSWORD) == registered_account


async def test_signup_accepts_same_password_for_different_logins(
    user_service: UserService, db_session: AsyncSession, registered_account: UserIdentity
) -> None:
    other_account = await user_service.signup_with_id()
    other_email = f"{uuid4().hex}@example.com"

    assert await user_service.signup(other_email, PASSWORD, other_account.system_id) == other_account

    first_user = await db_session.get(User, registered_account.id)
    second_user = await db_session.get(User, other_account.id)
    assert first_user is not None and first_user.password_hash
    assert second_user is not None and second_user.password_hash
    assert first_user.password_hash != second_user.password_hash
    assert await user_service.authenticate(other_email, PASSWORD) == other_account


async def test_signup_with_id_returns_new_identity(user_service: UserService) -> None:
    account = await user_service.signup_with_id()

    assert isinstance(account, UserIdentity)
    assert account.id > 0
    assert UUID(account.system_id).version == 4


async def test_authenticate_with_id_returns_none_for_null(user_service: UserService) -> None:
    assert await user_service.authenticate_with_id(None) is None


async def test_authenticate_with_id_returns_identity(user_service: UserService) -> None:
    account = await user_service.signup_with_id()

    assert await user_service.authenticate_with_id(account.system_id) == account


@pytest.mark.parametrize(
    ("login_is_correct", "password"),
    [
        (None, None),
        (None, PASSWORD),
        (True, None),
        (False, PASSWORD),
        (True, WRONG_PASSWORD),
        (False, WRONG_PASSWORD),
    ],
    ids=["both-null", "null-login", "null-password", "wrong-login", "wrong-password", "both-wrong"],
)
async def test_authenticate_returns_none_for_invalid_credentials(
    user_service: UserService,
    registered_account: UserIdentity,
    email: str,
    login_is_correct: bool | None,
    password: str | None,
) -> None:
    login = email if login_is_correct else f"unknown-{email}"
    if login_is_correct is None:
        login = None

    assert await user_service.authenticate(login, password) is None


async def test_authenticate_returns_identity_for_valid_credentials(
    user_service: UserService, registered_account: UserIdentity, email: str
) -> None:
    assert await user_service.authenticate(email, PASSWORD) == registered_account


async def test_signup_without_id_creates_classic_account(
    user_service: UserService, email: str
) -> None:
    account = await user_service.signup_without_id(email, PASSWORD)

    assert isinstance(account, UserIdentity)
    assert UUID(account.system_id).version == 4
    assert await user_service.authenticate(email, PASSWORD) == account
    assert await user_service.authenticate_with_id(account.system_id) is None


async def test_signup_without_id_rejects_duplicate_email(
    user_service: UserService, registered_account: UserIdentity, email: str
) -> None:
    with pytest.raises(LoginAlreadyExistsError):
        await user_service.signup_without_id(email, WRONG_PASSWORD)

    assert await user_service.authenticate(email, PASSWORD) == registered_account

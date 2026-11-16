"""Выпуск JWT и управление одноразовыми refresh-токенами."""

from datetime import datetime, timedelta, timezone

import jwt

from app.consts.consts import Consts
from hashlib import sha256
from secrets import token_urlsafe

from redis.asyncio import Redis
from redis.exceptions import RedisError

ROTATE_REFRESH_TOKEN = """
local user_id = redis.call('GET', KEYS[1])
if not user_id then return nil end

local expires_at = redis.call('PEXPIRETIME', KEYS[1])
if expires_at <= 0 then return nil end

if not redis.call('SET', KEYS[2], user_id, 'PXAT', expires_at, 'NX') then
    return redis.error_reply('Refresh token key collision')
end
redis.call('DEL', KEYS[1])
return user_id
"""


def refresh_key(token: str) -> str:
    """Формирует ключ Redis на основе хеша refresh-токена.

    Args:
        token: Исходный refresh-токен.

    Returns:
        Ключ Redis с префиксом и хешем SHA-256.
    """
    return Consts.REFRESH_KEY_PREFIX + sha256(token.encode()).hexdigest()


async def get_refresh_token(redis: Redis, user_id: int) -> str:
    """Выпускает refresh-токен и сохраняет его хеш в Redis с заданным временем жизни.

    Args:
        redis: Асинхронный клиент Redis.
        user_id: Внутренний ID пользователя.

    Returns:
        Refresh-токен для передачи клиенту.
    """
    token = token_urlsafe(32)
    if not await redis.set(
        refresh_key(token), str(user_id), ex=Consts.REFRESH_SESSION_LIFE_TIME, nx=True
    ):
        raise RedisError("Refresh token key collision")
    return token


async def rotate_refresh_token(redis: Redis, token: str) -> tuple[int, str] | None:
    """Заменяет использованный refresh-токен, сохраняя срок действия сессии.

    Args:
        redis: Асинхронный клиент Redis.
        token: Refresh-токен, полученный от клиента.

    Returns:
        Пара из ID пользователя и нового токена либо None, если старый токен недействителен.
    """
    new_token = token_urlsafe(32)
    user_id = await redis.eval(
        ROTATE_REFRESH_TOKEN, 2, refresh_key(token), refresh_key(new_token)
    )
    if user_id is None:
        return None
    return int(user_id), new_token


def create_access_token(user_id: int, *, secret_key: str) -> str:
    """Создаёт подписанный JWT с ID пользователя и сроком действия.

    Args:
        user_id: Внутренний ID пользователя.
        secret_key: Секретный ключ подписи.

    Returns:
        Access-токен в формате JWT.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=Consts.TOKEN_TIME_DELTA_IN_MINS
    )
    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at},
        secret_key,
        algorithm=Consts.JWT_ALGORITHM,
    )


def get_user_id_from_token(token: str, *, secret_key: str) -> int:
    """Проверяет подпись и срок действия JWT и извлекает ID пользователя.

    Args:
        token: Access-токен в формате JWT.
        secret_key: Секретный ключ для проверки подписи.

    Returns:
        Внутренний ID пользователя.

    Raises:
        jwt.InvalidTokenError: Токен недействителен или содержит некорректный ID.
    """
    claims = jwt.decode(
        token,
        secret_key,
        algorithms=[Consts.JWT_ALGORITHM],
        options={"require": ["sub", "exp"]},
    )

    try:
        return int(claims["sub"])
    except ValueError as exc:
        raise jwt.InvalidTokenError("Token subject must be a user ID") from exc

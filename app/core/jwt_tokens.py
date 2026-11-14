from datetime import datetime, timedelta, timezone

import jwt

from app.consts.consts import Consts


def create_access_token(user_id: int, *, secret_key: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=Consts.TOKEN_TIME_DELTA_IN_MINS
    )
    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at},
        secret_key,
        algorithm=Consts.JWT_ALGORITHM,
    )


def get_user_id_from_token(token: str, *, secret_key: str) -> int:
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

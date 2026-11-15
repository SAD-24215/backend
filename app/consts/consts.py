from dataclasses import dataclass
from datetime import timedelta


@dataclass
class Consts:
    TOKEN_TIME_DELTA_IN_MINS: int = 30
    JWT_ALGORITHM: str = "HS256"
    REFRESH_SESSION_TTL: str = timedelta(days=30)
    REFRESH_KEY_PREFIX: str = "auth:refresh:"

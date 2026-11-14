from dataclasses import dataclass


@dataclass
class Consts:
    TOKEN_TIME_DELTA_IN_MINS: int = 30
    JWT_ALGORITHM: str = "HS256"

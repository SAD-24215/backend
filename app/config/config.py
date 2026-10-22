from pydantic import PostgresDsn, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str
    debug: bool

    db_user: str
    db_password: str
    db_name: str
    db_port: str
    db_address: str
    db_container: str
    db_url_prefix: str

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"{self.db_url_prefix}{self.db_user}:{self.db_password}"
            f"@{self.db_address}:{self.db_port}/{self.db_name}"
        )


settings = Settings()

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str
    debug: bool
    app_host: str
    app_port: int
    jwt_secret_key: SecretStr | None = Field(default=None, min_length=32)

    db_user: str
    db_password: str
    db_name: str
    db_port: str
    db_address: str
    db_container: str
    db_url_prefix: str

    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_password: SecretStr | None = None

    @property
    def sqlalchemy_database_uri(self) -> str:
        return URL.create(
            drivername=self.db_url_prefix.removesuffix("://"),
            username=self.db_user,
            password=self.db_password,
            host=self.db_address,
            port=int(self.db_port),
            database=self.db_name,
        ).render_as_string(hide_password=False)


settings = Settings()

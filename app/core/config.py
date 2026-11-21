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

    test_db_user: str | None = None
    test_db_password: str | None = None
    test_db_name: str | None = None
    test_db_port: int | None = Field(default=None, ge=1, le=65535)
    test_db_address: str | None = None
    test_db_container: str | None = None

    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_password: SecretStr | None = None

    images_path: str

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

    @property
    def test_sqlalchemy_database_uri(self) -> str:
        """Собирает URL тестовой БД и проверяет, что он отличается от основного."""
        if not all(
            (
                self.test_db_user,
                self.test_db_password,
                self.test_db_name,
                self.test_db_port,
                self.test_db_address,
            )
        ):
            raise ValueError(
                "Заполните TEST_DB_USER, TEST_DB_PASSWORD, TEST_DB_NAME, "
                "TEST_DB_PORT и TEST_DB_ADDRESS для подключения к тестовой БД"
            )

        local_hosts = {"localhost", "127.0.0.1", "::1"}
        main_host = self.db_address.lower()
        test_host = self.test_db_address.lower()
        if main_host in local_hosts:
            main_host = "localhost"
        if test_host in local_hosts:
            test_host = "localhost"
        if (test_host, self.test_db_port, self.test_db_name) == (
            main_host,
            int(self.db_port),
            self.db_name,
        ):
            raise ValueError("Тестовая БД должна отличаться от основной БД")

        return URL.create(
            drivername=self.db_url_prefix.removesuffix("://"),
            username=self.test_db_user,
            password=self.test_db_password,
            host=self.test_db_address,
            port=self.test_db_port,
            database=self.test_db_name,
        ).render_as_string(hide_password=False)


settings = Settings()

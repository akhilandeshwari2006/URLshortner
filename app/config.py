from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    port: int
    database_url: str
    redis_url: str
    api_key_a: str
    api_key_b: str

    def validate_port(self) -> None:
        if self.port < 1 or self.port > 65535:
            raise ValueError("Invalid PORT. Set PORT in .env (example: PORT=8000).")

    def validate_database_url(self) -> None:
        if not self.database_url:
            raise ValueError("Invalid DATABASE_URL. Set DATABASE_URL in .env.")


settings = Settings()
settings.validate_port()
settings.validate_database_url()
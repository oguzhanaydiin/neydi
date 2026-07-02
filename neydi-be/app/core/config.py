from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "neydi-be"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()

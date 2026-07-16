import re
from typing import Literal
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _host_from_supabase_url(url: str) -> str:
    """https://<ref>.supabase.co -> db.<ref>.supabase.co"""
    parsed = urlparse(url.strip())
    host = parsed.hostname or ""
    match = re.fullmatch(r"(.+)\.supabase\.co", host)
    if not match:
        raise ValueError(f"Invalid SUPABASE_URL host: {host!r} (expected <ref>.supabase.co)")
    return f"db.{match.group(1)}.supabase.co"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    APP_NAME: str = "neydi-be"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 90

    # local = Docker/local Postgres  |  supabase = cloud Postgres
    DB_MODE: Literal["local", "supabase"] = "local"

    # Used when DB_MODE=local (unchanged — Docker compose overrides HOST/PORT)
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    # Supabase — Connect page: Project URL + API keys (REST client, not used for SQLAlchemy)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Supabase Postgres — Settings → Database → Database password (NOT the API key)
    SUPABASE_DB_PASSWORD: str = ""
    SUPABASE_POSTGRES_USER: str = "postgres"
    SUPABASE_POSTGRES_HOST: str = ""
    SUPABASE_POSTGRES_PORT: int = 5432
    SUPABASE_POSTGRES_DB: str = "postgres"

    # Optional superadmin bootstrap — set both to auto-create the superadmin account on startup.
    SUPERADMIN_EMAIL: str | None = None
    SUPERADMIN_PASSWORD: str | None = None
    SUPERADMIN_USERNAME: str = "neydi"

    @model_validator(mode="after")
    def validate_supabase_config(self) -> "Settings":
        if self.DB_MODE != "supabase":
            return self

        if not self.SUPABASE_DB_PASSWORD:
            raise ValueError(
                "SUPABASE_DB_PASSWORD is required when DB_MODE=supabase. "
                "Find it in Supabase → Settings → Database (this is NOT SUPABASE_KEY)."
            )

        if not self.SUPABASE_POSTGRES_HOST and not self.SUPABASE_URL:
            raise ValueError(
                "Set SUPABASE_URL (from Connect page) or SUPABASE_POSTGRES_HOST when DB_MODE=supabase"
            )

        return self

    @property
    def db_ssl(self) -> bool:
        return self.DB_MODE == "supabase"

    @property
    def _supabase_host(self) -> str:
        if self.SUPABASE_POSTGRES_HOST:
            return self.SUPABASE_POSTGRES_HOST
        return _host_from_supabase_url(self.SUPABASE_URL)

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_MODE == "supabase":
            user = self.SUPABASE_POSTGRES_USER
            password = self.SUPABASE_DB_PASSWORD
            host = self._supabase_host
            port = self.SUPABASE_POSTGRES_PORT
            db = self.SUPABASE_POSTGRES_DB
        else:
            user = self.POSTGRES_USER
            password = self.POSTGRES_PASSWORD
            host = self.POSTGRES_HOST
            port = self.POSTGRES_PORT
            db = self.POSTGRES_DB

        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


settings = Settings()

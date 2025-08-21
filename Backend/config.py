# config.py
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Which environment we are running in
    APP_ENV: Literal["local", "staging", "prod"] = "local"

    # HTTP basics
    BASE_URL: str = "http://127.0.0.1:8000"    # default for local dev
    BASE_HOST: str = "0.0.0.0"
    BASE_PORT: int = 8000

    # If you’re hosting your API behind a subpath (e.g., /reporter)
    # set ROOT_PATH="/reporter" in prod so FastAPI generates correct URLs.
    ROOT_PATH: str = ""  # "" in local; "/reporter" (example) in prod

    # CORS: comma-separated in env → parsed into list
    ALLOW_ORIGINS: list[str] = [
    "http://localhost:5173",     # vite dev server
    "http://127.0.0.1:5173",
    ]

    # JWT from dashboard
    DASHBOARD_JWT_ALG: Literal["HS256", "RS256"] = "HS256"
    DASHBOARD_JWT_SECRET: str = "CHANGE_ME"              # HS256 only
    DASHBOARD_JWT_PUBLIC_KEY: str | None = None          # RS256 only (PEM)

    # Rate limiting, etc. (example)
    RATE_LIMIT: str = "10/second"

    # Celery (example)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    model_config = SettingsConfigDict(
        env_file=(".env",),          # local dev
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def allow_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOW_ORIGINS.split(",") if o.strip()]

settings = Settings()

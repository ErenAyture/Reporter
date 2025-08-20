from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BASE_URL: str = "http://127.0.0.1:8000"    # default for local dev
    BASE_PORT: int = 8000
    BASE_HOST: str = "0.0.0.0"
    ALLOW_ORIGINS: list[str] = [
    "http://localhost:5173",     # vite dev server
    "http://127.0.0.1:5173",
    ]
    DASHBOARD_JWT_ALG: str = "HS256"             # or "RS256"
    DASHBOARD_JWT_SECRET: str = "CHANGE_ME"      # HS256 only
    DASHBOARD_JWT_PUBLIC_KEY: str | None = None  # RS256 public key (PEM)
    class Config:
        env_file = ".env"                  # if you read from .env
        env_file_encoding = "utf-8"
    # …any other shared config

settings = Settings()   
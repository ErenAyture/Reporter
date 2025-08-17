from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BASE_URL: str = "http://127.0.0.1:8000"    # default for local dev
    BASE_PORT: int = 8000
    BASE_HOST: str = "0.0.0.0"
    class Config:
        env_file = ".env"                  # if you read from .env
        env_file_encoding = "utf-8"
    # …any other shared config

settings = Settings()   
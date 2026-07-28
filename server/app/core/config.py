from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application settings
    APP_NAME: str =  "AI-Workflow-Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False 

    # Database settings
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int

    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]  # Allow all origins by default

settings = Settings()
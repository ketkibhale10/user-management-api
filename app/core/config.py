from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Override any value via environment or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "User Management API"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./users.db"

    # JWT
    SECRET_KEY: str = "dev-secret-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS (JSON list in env, e.g. ["http://localhost:3000"])
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Seeded admin (created on first startup)
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "Admin@12345"
    ADMIN_NAME: str = "System Admin"

    LOG_LEVEL: str = "INFO"


settings = Settings()
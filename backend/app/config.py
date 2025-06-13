import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App settings
    app_name: str = "Morse-Me-Backend"
    app_port: int = 8000
    admin_email: str = "admin@morse-me.com"

    # API settings
    api_v1_str: str = "/api/v1"

    # CORS settings - for development, allow common localhost ports
    allowed_hosts: list[str] = [
        "http://localhost:3000",  # Nuxt.js default
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative port
        "http://localhost:8080",  # Vue/other frameworks
        "http://localhost:8081",
        "http://localhost:4200",  # Angular default
        "http://localhost:5173",  # Vite default
    ]

    # For development only - set to True to allow all origins
    development_mode: bool = True

    # Database settings
    database_url: str = "postgresql://morse_user:morse_password@localhost:5432/morse_me_db"

    # JWT settings
    secret_key: str = "super-secret-key-default-value-change-this"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Point to shared .env in project root. or use ENV_FILE if specified otherwise
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", "../.env"),
        env_prefix="BACKEND_",
        extra="ignore"
    )

    # Convenience property for FastAPI compatibility
    @property
    def API_V1_STR(self) -> str:
        return self.api_v1_str

settings = Settings()

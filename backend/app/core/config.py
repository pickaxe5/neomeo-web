from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://neomeo:neomeo@localhost:5432/neomeo"

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, value: str) -> str:
        """Render 등 매니지드 Postgres는 postgres://·postgresql:// 스킴을 준다.
        psycopg3 드라이버를 쓰도록 스킴만 맞춰준다."""
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14

    github_client_id: str = ""
    github_client_secret: str = ""
    github_oauth_callback_url: str = "http://localhost:8000/auth/github/callback"

    demo_account_email: str = "demo@neomeo.dev"
    demo_account_password: str = "demo-password-change-me"

    poll_interval_minutes: int = 10

    frontend_base_url: str = "http://localhost:3000"


settings = Settings()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://agent:agentpass@db:5432/email_agent"
    REDIS_URL: str = "redis://redis:6379/0"
    REVIEWER_USER: str = "reviewer"
    REVIEWER_PASSWORD: str = "reviewer123"
    # Auth
    JWT_SECRET: str = "change_me_super_secret"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 1440
    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    # IMAP
    IMAP_HOST: str = ""
    IMAP_USER: str = ""
    IMAP_PASSWORD: str = ""
    IMAP_FOLDER: str = "INBOX"

    # SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@logistics.local"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    APP_BASE_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()
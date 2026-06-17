from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI Due Diligence Copilot"
    APP_ENV: str = "development"

    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ai_due_diligence"

    REDIS_URL: str = "redis://localhost:6379/0"

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "ai-due-diligence-docs"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    STORAGE_BACKEND: str = "local"  # "local" for dev, "s3" for production
    LOCAL_UPLOAD_DIR: str = "uploads"

    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = (".env.local", ".env")
        extra = "ignore"


settings = Settings()

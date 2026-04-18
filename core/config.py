from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # Secrets (from .env)
    SECRET_KEY: str = ""
    DB_PASSWORD: str = ""
    
    # Configuration with defaults
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "youtube_db"
    DB_USER: str = "postgres"

settings = Settings()
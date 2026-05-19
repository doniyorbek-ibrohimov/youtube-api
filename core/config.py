from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # 🔒 REQUIRED (no defaults)
    SECRET_KEY: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str

    # ⚙️ OPTIONAL (safe defaults)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    MINIO_ENDPOINT: str = "http://localhost:9000"
    MINIO_BUCKET_NAME: str = "youtube-videos"
    MINIO_SECURE: bool = False

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
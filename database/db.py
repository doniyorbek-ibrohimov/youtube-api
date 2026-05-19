from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase, Session
from typing import Generator
from core.config import settings



# DB setup
DATABASE_URL = (f"postgresql+psycopg://{settings.DB_USER}:"
    f"{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/"
    f"{settings.DB_NAME}"
)


# Engine (connection with DB)
engine = create_engine(
    DATABASE_URL,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False, 
    autocommit=False,
)

class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


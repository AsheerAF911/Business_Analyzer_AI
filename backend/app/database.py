from pathlib import Path
import os
from app.models import Base

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load backend/.env
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME = os.getenv("DATABASE_NAME", "business_ai")

if not DATABASE_USER or not DATABASE_PASSWORD:
    raise RuntimeError(
        "DATABASE_USER and DATABASE_PASSWORD must be set in backend/.env"
    )

DATABASE_URL = (
    f"postgresql+psycopg://{DATABASE_USER}:"
    f"{DATABASE_PASSWORD}@{DATABASE_HOST}:"
    f"{DATABASE_PORT}/{DATABASE_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
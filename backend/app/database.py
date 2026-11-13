from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from urllib.parse import quote_plus

# Update with your MySQL credentials OR set environment variables
DB_USER     = os.getenv("DB_USER",     "root")  # set to your MySQL user
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin@123")  # your MySQL password
DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("DB_PORT",     "3306")
DB_NAME     = os.getenv("DB_NAME",     "hackathon_db")

raw_db_url = os.getenv("DATABASE_URL")
if raw_db_url:
    if raw_db_url.startswith("mysql://"):
        raw_db_url = raw_db_url.replace("mysql://", "mysql+pymysql://", 1)
    SQLALCHEMY_DATABASE_URL = raw_db_url
else:
    encoded_password = quote_plus(DB_PASSWORD)
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency – yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

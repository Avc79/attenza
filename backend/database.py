import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Use DATABASE_URL from environment, or fallback to sqlite local
SQL_ALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./attendance.db")

# For PostgreSQL, we might need to fix the prefix if it's "postgres://" (Heroku/older Supabase)
if SQL_ALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQL_ALCHEMY_DATABASE_URL = SQL_ALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(SQL_ALCHEMY_DATABASE_URL)
# For SQLite, we need check_same_thread: False
if SQL_ALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQL_ALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

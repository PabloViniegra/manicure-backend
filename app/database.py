import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

"""
Database configuration and session management for the application.

- Loads the database URL from environment variables.
- Sets up the SQLAlchemy async engine and session maker.
- Provides a declarative base for models.
- Exposes a dependency to get a database session for FastAPI routes.
"""

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


async def get_db():
    """
    Dependency that provides a SQLAlchemy async database session.

    Yields:
        AsyncSession: An active database session for use in FastAPI endpoints.
    """
    async with async_sessionmaker() as session:
        yield session

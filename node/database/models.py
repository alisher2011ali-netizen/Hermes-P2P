from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import (
    String,
    Text,
    Float,
    DateTime,
    func,
)
from datetime import datetime
from urllib.parse import quote_plus
from pathlib import Path
import asyncio


class Base(DeclarativeBase):
    pass


class RelayMessage(Base):
    __tablename__ = "relay_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_pubkey: Mapped[str] = mapped_column(String(100), index=True)
    to_pubkey: Mapped[str] = mapped_column(String(100))
    message_type: Mapped[str] = mapped_column(String(10), default="TEXT")
    payload: Mapped[str] = mapped_column(Text)
    file_id: Mapped[str] = mapped_column(String(255), nullable=True)
    file_size: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


user = "hermes_user"
password = "alisher2011%"
host = "localhost"
db = "hermes_db"


DATABASE_URL = f"postgresql+asyncpg://{user}:{quote_plus(password)}@{host}/{db}"
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_profile_db():
    """Инициализирует таблицы."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()


asyncio.create_task(init_profile_db())

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from pathlib import Path

from app.database.models import MainBase, Base, Account, Identity, Contact, Message

main_engine = create_async_engine("sqlite+aiosqlite:///./data/main.db")
main_session_factory = async_sessionmaker(main_engine, expire_on_commit=False)


def get_session_factory(db_path: Path):
    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(db_url)
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_main_db():
    """Создает основную базу реестра профилей."""
    main_engine = create_async_engine("sqlite+aiosqlite:///./data/main.db")
    async with main_engine.begin() as conn:
        await conn.run_sync(MainBase.metadata.create_all)
    await main_engine.dispose()


async def init_profile_db(db_path: Path):
    """Создает файл БД для конкретного профиля и инициализирует таблицы."""
    db_url = f"sqlite+aiosqlite:///{db_path}"
    profile_engine = create_async_engine(db_url)

    async with profile_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await profile_engine.dispose()

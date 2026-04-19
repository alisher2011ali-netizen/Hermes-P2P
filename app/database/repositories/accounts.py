import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.main_models import Account


async def get_all_accounts(session: AsyncSession):
    result = await session.execute(sa.select(Account))
    return result.scalars().all()


async def get_account_by_name(session: AsyncSession, name: str):
    result = await session.execute(sa.select(Account).filter_by(display_name=name))
    return result.scalars().first()

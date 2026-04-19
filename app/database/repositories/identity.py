import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from app.database.models.secondary_models import Identity


async def create_new_identity(
    session: AsyncSession, identity_data: Identity
) -> Identity:
    session.add(identity_data)
    return identity_data


async def get_identity_by_name(session: AsyncSession, name: str) -> Identity:
    result = await session.execute(sa.select(Identity).filter_by(name=name))
    return result.scalars().first()

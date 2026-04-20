import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List

from app.database.models.secondary_models import Message


async def save_message(
    session: AsyncSession,
    new_msg: Message
):
    """Сохраняет зашифрованное сообщение."""
    session.add(new_msg)
    await session.commit()
    return new_msg


async def get_messages_by_contact_id(
    session: AsyncSession, contact_id: int
) -> List[Message]:
    result = await session.execute(sa.select(Message).filter_by(contact_id=contact_id))
    return result.scalars().all()

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List

from app.database.models.secondary_models import Message


async def save_message(
    session: AsyncSession,
    contact_id: int,
    encypted_content: bytes,
    nonce: bytes,
    signature_bytes: bytes,
    timestamp: datetime,
    is_outbox: bool,
):
    """Сохраняет зашифрованное сообщение."""
    new_msg = Message(
        contact_id=contact_id,
        encrypted_content=encypted_content,
        nonce=nonce,
        signature_bytes=signature_bytes,
        timestamp=timestamp,
        is_outbox=is_outbox,
    )
    session.add(new_msg)
    return new_msg


async def get_messages_by_contact_id(
    session: AsyncSession, contact_id: int
) -> List[Message]:
    result = await session.execute(sa.select(Message).filter_by(contact_id=contact_id))
    return result.scalars().all()

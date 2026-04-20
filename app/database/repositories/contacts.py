import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc
from typing import List

from app.database.models.secondary_models import Contact, Message


async def add_contact(session: AsyncSession, contact: Contact):
    session.add(contact)
    await session.commit()
    return contact


async def get_all_contacts(session: AsyncSession) -> List[Contact]:
    result = await session.execute(
        sa.select(Contact).order_by(Contact.last_message_time())
    )
    contacts = result.scalars().all()

    for c in contacts:
        session.expunge(c)

    return contacts


async def get_contact_by_id(session: AsyncSession, contact_id: int) -> Contact:
    result = await session.execute(sa.select(Contact).filter_by(id=contact_id))
    return result.scalars().first()


async def get_contacts_with_last_message(
    session: AsyncSession,
) -> List:
    last_msg_subq = sa.select(
        Message.id,
        Message.contact_id,
        Message.encrypted_text,
        Message.nonce,
        Message.timestamp,
        func.row_number()
        .over(partition_by=Message.contact_id, order_by=desc(Message.timestamp))
        .label("rn"),
    ).subquery()

    unread_subq = (
        sa.select(Message.contact_id, func.count(Message.id).label("unread_count"))
        .filter(Message.is_read == False)
        .group_by(Message.contact_id)
        .subquery()
    )

    stmt = (
        sa.select(
            Contact,
            last_msg_subq.c.encrypted_text,
            last_msg_subq.c.nonce,
            last_msg_subq.c.timestamp,
            func.coalesce(unread_subq.c.unread_count, 0).label("unread_count"),
        )
        .outerjoin(
            last_msg_subq,
            (Contact.id == last_msg_subq.c.contact_id) & (last_msg_subq.c.rn == 1),
        )
        .outerjoin(unread_subq, Contact.id == unread_subq.c.contact_id)
    )

    result = await session.execute(stmt)
    return result.all()

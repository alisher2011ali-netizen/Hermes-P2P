from app.state import state
from app.database.models.secondary_models import Contact
from app.ui import builder


async def get_chat_tile(data: list):
    contact: Contact = data[0]
    text = await state.crypto.decrypt_from(
        sender_public_key_bytes=contact.public_key,
        ciphertext=data[1],
        nonce=data[2],
    )
    timestamp = data[3]
    unread_count = data[4]
    return builder.create_chat_tile(
        contact=contact, text=text, timestamp=timestamp, unread_count=unread_count
    )

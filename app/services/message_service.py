from datetime import datetime
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.crypto import CryptoManager
from app.database.models.secondary_models import Message
from app.database.repositories import messages
from app.database.repositories import contacts
from app.network import network_manager
from app.network.network_manager import MessagePacket
from app.state import state


class MessageService:
    async def send_message(contact_id: int, text: str):
        async with state.session_factory() as session:
            contact = await contacts.get_contact_by_id(
                session=session, contact_id=contact_id
            )

        ciphertext, nonce = state.crypto.encrypt_for(
            recipient_public_key_bytes=contact.public_key, message=text
        )
        signature = state.crypto.sign_ciphertext(ciphertext)

        msg = Message(
            contact_id=contact_id,
            encrypted_text=ciphertext,
            nonce=nonce,
            signature=signature,
            is_outbox=True,
        )
        async with state.session_factory() as session:
            await messages.save_message(session=session, new_msg=msg)

        packet = MessagePacket(
            to_pubkey=contact.public_key.hex(),
            from_pubkey=state.crypto.public_key_bytes.hex(),
            payload=ciphertext.hex(),
            nonce=nonce.hex(),
            signature=signature.hex(),
            timestamp=datetime.now().isoformat(),
        )
        try:
            await network_manager.send_packet(packet=packet)
            return True
        except Exception as err:
            raise f"Не удалось отправить сообщение: {err}"

    @classmethod
    async def polling_message(
        current_session_factory: async_sessionmaker, packet: dict
    ):
        async with current_session_factory() as session:
            c = contacts.get_contact_by_pubkey(
                session=session, contact_pubkey=bytes.fromhex(packet["from_pubkey"])
            )
            if CryptoManager.verify_message(
                message=packet["payload"], signature=packet["signature"]
            ):
                new_msg = Message(
                    contact_id=c.id,
                    encrypted_text=bytes.fromhex(packet["payload"]),
                    nonce=bytes.fromhex(packet["nonce"]),
                    signature=bytes.fromhex(packet["signature"]),
                    timestamp=datetime.fromisoformat(packet["timestmap"]),
                )

                await messages.save_message(session=session, new_msg=new_msg)

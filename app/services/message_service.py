from datetime import datetime

from app.core.crypto import CryptoManager
from app.database.models.secondary_models import Message
from app.database.repositories import messages
from app.database.repositories import contacts
from app.network import network_manager
from app.network.network_manager import MessagePacket
from app.state import state


class MessageService:
    def __init__(self):
        self.crypto: CryptoManager = state.crypto
        self.session_factory = state.session_factory

    async def send_message(self, contact_id: int, text: str):
        async with self.session_factory() as session:
            contact = await contacts.get_contact_by_id(
                session=session, contact_id=contact_id
            )

        ciphertext, nonce = self.crypto.encrypt_for(
            recipient_public_key_bytes=contact.public_key, message=text
        )
        signature = self.crypto.sign_ciphertext(ciphertext)

        msg = Message(
            contact_id=contact_id,
            encrypted_text=ciphertext,
            nonce=nonce,
            signature=signature,
            is_outbox=True,
        )
        async with self.session_factory() as session:
            await messages.save_message(session=session, new_msg=msg)

        packet = MessagePacket(
            to_pubkey=contact.public_key.hex(),
            from_pubkey=self.crypto.public_key_bytes.hex(),
            payload=ciphertext.hex(),
            nonce=nonce.hex(),
            signature=signature.hex(),
            timestamp=datetime.now().isoformat(),
        )
        await network_manager.send_packet(packet=packet)

    async def polling_message(self, packet: dict):
        async with state.session_factory() as session:
            c = contacts.get_contact_by_pubkey(
                session=session, contact_pubkey=bytes.fromhex(packet["from_pubkey"])
            )
            if state.crypto.verify_message(
                message=packet["payload"], signature=packet["signature"]
            ):
                new_msg = Message(
                    contact_id=c.id,
                    encrypted_text=bytes.fromhex(packet["payload"]),
                    nonce=bytes.fromhex(packet["nonce"]),
                    signature=bytes.fromhex(packet["signature"]),
                    timestamp=datetime.fromisoformat(packet["timestmap"]),
                )
                async with state.session_factory() as session:
                    await messages.save_message(session=session, new_msg=new_msg)

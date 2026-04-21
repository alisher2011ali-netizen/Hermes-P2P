from app.core.crypto import CryptoManager
from app.database.models.secondary_models import Message
from app.database.repositories import messages
from app.database.repositories import contacts
from app.network import network_manager
from app.state import state


class Message_service:
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

        packet = {
            "to_pubkey": contact.public_key.hex(),
            "from_pubkey": self.crypto.public_key_bytes.hex(),
            "payload": ciphertext.hex(),
            "nonce": nonce.hex(),
            "signature": signature.hex(),
        }
        await network_manager.send_packet(packet=packet)

    async def polling_message(self, packet: dict):
        pass

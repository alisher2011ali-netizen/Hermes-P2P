from app.network.p2p_node import MessagePacket
from app.database.manager import DBManager
from app.core.crypto import CryptoManager


class MessageService:
    def __init__(self, db: DBManager, crypto: CryptoManager):
        self.db = db
        self.crypto = crypto

    async def process_incoming(self, packet: MessagePacket):
        contact = await self.db.get_contact_by_onion(packet.sender_onion)
        if not contact:
            raise Exception("Contact not found")

        ciphertext_bytes = bytes.fromhex(packet.ciphertext)
        nonce_bytes = bytes.fromhex(packet.nonce)
        signature_bytes = bytes.fromhex(packet.signature)

        decrypted_text = self.crypto.decrypt_from(
            contact.public_key, ciphertext_bytes, nonce_bytes
        )

        await self.db.save_message(
            sender_name=contact.alias,
            contact_id=contact.id,
            content=ciphertext_bytes,
            nonce=nonce_bytes,
            signature_bytes=signature_bytes,
            is_outbox=False,
        )

        print(decrypted_text)

from pydantic import BaseModel

from app.network.protocol import HermesProtocol
from app.database.manager import DBManager
from app.core.crypto import CryptoManager


class MessagePacket(BaseModel):
    sender_onion: str
    ciphertext: str
    nonce: str
    signature: str


class MessageService:
    def __init__(self, db: DBManager, crypto: CryptoManager):
        self.db = db
        self.crypto = crypto
        self.protocol = HermesProtocol()

    async def process_incoming(self, packet: MessagePacket):
        contact = await self.db.get_contact_by_onion(packet.sender_onion)
        if not contact:
            raise Exception("Contact not found")

        ciphertext_bytes = bytes.fromhex(packet.ciphertext)
        nonce_bytes = bytes.fromhex(packet.nonce)
        signature_bytes = bytes.fromhex(packet.signature)

        await self.db.save_message(
            contact_id=contact.id,
            encrypted_content=ciphertext_bytes,
            nonce=nonce_bytes,
            signature_bytes=signature_bytes,
            is_outbox=False,
        )

    async def process_outgoing(self, target_onion: str, packet: MessagePacket):
        contact = await self.db.get_contact_by_onion(target_onion)
        if not contact:
            raise Exception("Contact not found")

        await self.protocol.send_payload(target_onion=target_onion, packet=packet)

        ciphertext_bytes = bytes.fromhex(packet.ciphertext)
        nonce_bytes = bytes.fromhex(packet.nonce)
        signature_bytes = bytes.fromhex(packet.signature)

        await self.db.save_message(
            contact_id=contact.id,
            encrypted_content=ciphertext_bytes,
            nonce=nonce_bytes,
            signature_bytes=signature_bytes,
            is_outbox=True,
        )

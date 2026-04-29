from datetime import datetime

from app.core.crypto import CryptoManager
from app.database.models import Message
from app.database.repositories import messages
from app.database.repositories import contacts
from app.network.network_manager import network_manager
from app.network.network_manager import MessagePacket
from app.state import state


class MessageService:
    on_message_received = None

    @staticmethod
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
            payload=ciphertext,
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
        success = await network_manager.send_packet(packet=packet)
        if not success:
            print("Ошибка отправки на сервер")
        return success

    @staticmethod
    async def send_media(contact_id: int, file_path: str):
        encrypted_file, file_key = CryptoManager.get_encrypted_file_and_file_key(
            file_path=file_path
        )

        file_id = network_manager.upload_file(encrypted_file)

        async with state.session_factory() as session:
            contact = await contacts.get_contact_by_id(session, contact_id)

        encrypted_key, nonce = state.crypto.encrypt_for(
            recipient_public_key_bytes=contact.public_key, message=file_key
        )
        signature = state.crypto.sign_ciphertext(encrypted_key)

        packet = MessagePacket(
            to_pubkey=contact.public_key.hex(),
            from_pubkey=state.crypto.public_key_bytes.hex(),
            msg_type="MEDIA",
            payload=encrypted_key.hex(),
            file_id=file_id,
            nonce=nonce.hex,
            signature=signature.hex(),
            timestamp=datetime.now().isoformat(),
        )
        await network_manager.send_packet(packet)

    @classmethod
    async def polling_message(cls, packet: MessagePacket):
        """Обработка входящего пакета от Relay-сервера."""

        if not state.session_factory or not state.crypto:
            return

        async with state.session_factory() as session:
            c = contacts.get_contact_by_pubkey(
                session=session, contact_pubkey=bytes.fromhex(packet.from_pubkey)
            )
            if not c:
                return

            if CryptoManager.verify_message(
                message=packet.payload, signature=packet.signature
            ):
                new_msg = Message(
                    contact_id=c.id,
                    payload=bytes.fromhex(packet.payload),
                    nonce=bytes.fromhex(packet.nonce),
                    signature=bytes.fromhex(packet.signature),
                    is_outbox=False,
                    timestamp=datetime.fromisoformat(packet.timestamp),
                )

                await messages.save_message(session=session, new_msg=new_msg)

                if cls.on_message_received:
                    await cls.on_message_received()

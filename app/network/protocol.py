import httpx

from app.database.models import Identity
from app.database.manager import DBManager
from app.core.crypto import CryptoManager


class HermesProtocol:
    def __init__(self, tor_proxy="socks5://tor:9050"):
        self.proxy = tor_proxy

    async def send_payload(
        self,
        target_onion: str,
        recipient_pubkey: bytes,
        message_text: str,
        identity: Identity,
        crypto: CryptoManager,
        db: DBManager,
    ):
        """Отправляет данные на чужой .onion адрес"""
        encrypted_bytes, nonce_bytes = crypto.encrypt_for(
            recipient_public_key_bytes=recipient_pubkey, message=message_text
        )

        signature_bytes = crypto.sign_message(encrypted_bytes.hex())

        packet = {
            "sender": identity.display_name,
            "sender_pubkey": crypto.public_key_bytes.hex(),
            "signature": signature_bytes.hex(),
            "payload": {
                "cipher_text": encrypted_bytes.hex(),
                "nonce": nonce_bytes.hex(),
            },
        }

        await db.save_message(
            sender_name=identity.display_name,
            target_onion=target_onion,
            content=encrypted_bytes,
            nonce=nonce_bytes,
            signature_bytes=signature_bytes,
            is_outbox=True,
        )

        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        async with httpx.AsyncClient(
            proxy=self.proxy, limits=limits, timeout=30.0
        ) as client:
            url = f"http://{target_onion}/receive_message"
            try:
                response = await client.post(url, json=packet)

                if response.status_code == 200:
                    print(f"[+] Сообщение для {target_onion} успешно отправлено")
                    return True
                else:
                    print(f"[-] Ошибка узла: {response.status_code}")
                    return False
            except httpx.RequestError as exc:
                print(f"[-] Не удалось связаться с узлом {target_onion}: {exc}")
                return False

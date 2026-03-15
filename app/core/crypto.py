import nacl.utils
from nacl.public import PrivateKey, PublicKey, Box
from nacl.signing import SigningKey, VerifyKey
from nacl.secret import SecretBox
from nacl.pwhash.argon2id import kdf, OPSLIMIT_MODERATE, MEMLIMIT_MODERATE, SALTBYTES
from typing import Tuple, Optional


class CryptoManager:
    """Управление ключами, E2EE шифрованием и цифровыми подписями."""

    def __init__(
        self,
        private_key_bytes: Optional[bytes] = None,
        signing_key_bytes: Optional[bytes] = None,
    ):
        if private_key_bytes:
            self._private_key = PrivateKey(private_key_bytes)
        else:
            self._private_key = PrivateKey.generate()

        if signing_key_bytes:
            self._signing_key = SigningKey(signing_key_bytes)
        else:
            self._signing_key = SigningKey.generate()

        self.public_key = self._private_key.public_key
        self.verify_key = self._signing_key.verify_key

    @property
    def private_key_bytes(self) -> bytes:
        return bytes(self._private_key)

    @property
    def signing_key_bytes(self) -> bytes:
        return bytes(self._signing_key)

    @property
    def public_key_bytes(self) -> bytes:
        return bytes(self.public_key)

    @property
    def verify_key_bytes(self) -> bytes:
        return bytes(self.verify_key)

    def encrypt_for(
        self, recipient_public_key_bytes: bytes, message: str
    ) -> Tuple[bytes, bytes]:
        """
        Шифрует сообщение для получателя.
        Возвращает кортеж: (зашифрованное сообщение, nonce).
        """
        recipient_pub = PublicKey(recipient_public_key_bytes)
        box = Box(self._private_key, recipient_pub)

        nonce = nacl.utils.random(Box.NONCE_SIZE)
        encrypted = box.encrypt(message.encode("utf-8"), nonce)

        return encrypted.ciphertext, nonce

    def decrypt_from(
        self, sender_public_key_bytes: bytes, ciphertext: bytes, nonce: bytes
    ) -> str:
        """Расшифровывает входящее сообщение."""
        sender_pub = PublicKey(sender_public_key_bytes)
        box = Box(self._private_key, sender_pub)

        decrypted = box.decrypt(ciphertext, nonce)
        return decrypted.decode("utf-8")

    @staticmethod
    def generate_signing_pair() -> Tuple[bytes, bytes]:
        """Генерирует пару ключей для цифровой подписи (ED25519)."""
        signing_key = SigningKey.generate()
        return bytes(signing_key), bytes(signing_key.verify_key)

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes) -> bytes:
        """Генерирует криптографический ключ из обычного пароля (Argon2id)."""
        return kdf(
            SecretBox.KEY_SIZE,
            password.encode("utf-8"),
            salt,
            opslimit=OPSLIMIT_MODERATE,
            memlimit=MEMLIMIT_MODERATE,
        )

    def encrypt_all_keys(self, password: str) -> Tuple[bytes, bytes]:
        """Шифрует приватный ключ и подпись-ключ мастер-паролем."""
        salt = nacl.utils.random(SALTBYTES)
        key = self.derive_key_from_password(password, salt)
        box = SecretBox(key)
        nonce = nacl.utils.random(SecretBox.NONCE_SIZE)

        combined_keys = bytes(self._private_key) + bytes(self._signing_key)

        encrypted = box.encrypt(combined_keys, nonce)

        return encrypted.ciphertext, salt, nonce

    @classmethod
    def decrypt_all_keys(
        cls, encrypted_blob: bytes, password: str, salt: bytes, nonce: bytes
    ):
        """Восстанавливает приватный ключ и подпись-ключ из зашифрованных данных и возвращает объект CryptoManager."""

        key = cls.derive_key_from_password(password, salt)
        box = SecretBox(key)

        try:
            decrypted_combined = box.decrypt(encrypted_blob, nonce)

            priv_bytes = decrypted_combined[:32]
            sign_bytes = decrypted_combined[32:]

            return cls(private_key_bytes=priv_bytes, signing_key_bytes=sign_bytes)
        except Exception:
            return ValueError("Неверный пароль или поврежденные данные!")

    def sign_message(self, message_hex: str) -> bytes:
        """Создает цифровую подпись для сообщения."""
        return self._signing_key.sign(message_hex.encode("utf-8")).signature

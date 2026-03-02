import nacl.utils
from nacl.public import PrivateKey, PublicKey, Box
from nacl.signing import SigningKey, VerifyKey
from nacl.secret import SecretBox
from typing import Tuple, Optional


class CryptoManager:
    """Управление ключами, E2EE шифрованием и цифровыми подписями."""

    def __init__(self, private_key_bytes: Optional[bytes] = None):
        if private_key_bytes:
            self._private_key = PrivateKey(private_key_bytes)
        else:
            self._private_key = PrivateKey.generate()

        self.public_key = self._private_key.public_key

    @property
    def private_key_bytes(self) -> bytes:
        return bytes(self._private_key)

    @property
    def public_key_bytes(self) -> bytes:
        return bytes(self.public_key)

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
        return nacl.pwhash.argon2id.kdf(
            SecretBox.KEY_SIZE,
            password.encode("utf-8"),
            salt,
            opslimit=nacl.pwhash.argon2id.OPSLIMIT_MODERATE,
            memlimit=nacl.pwhash.argon2id.MEMLIMIT_MODERATE,
        )

    def encrypt_private_key(self, password: str) -> Tuple[bytes, bytes]:
        """Шифрует приватный ключ мастер-паролем."""
        salt = nacl.utils.random(nacl.pwhash.argon2id.SALTBYTES)
        key = self.derive_key_from_password(password, salt)

        box = SecretBox(key)
        nonce = nacl.utils.random(SecretBox.NONCE_SIZE)

        encrypted = box.encrypt(self.private_key_bytes, nonce)

        return encrypted.ciphertext, salt, nonce

    def decrypt_private_key(
        cls, encrypted_key: bytes, password: str, salt: bytes, nonce: bytes
    ):
        """Восстанавливает приватный ключ из зашифрованных данных."""

        key = cls.derive_key_from_password(password, salt)

        box = SecretBox(key)

        try:
            decrypted_private_bytes = box.decrypt(encrypted_key, nonce)
            return cls(decrypted_private_bytes)
        except Exception:
            return None

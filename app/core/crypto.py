import nacl.utils
from nacl.encoding import HexEncoder
from nacl.public import PrivateKey, PublicKey, Box
from nacl.signing import SigningKey, VerifyKey
from nacl.secret import SecretBox
from nacl.pwhash.argon2id import kdf, OPSLIMIT_MODERATE, MEMLIMIT_MODERATE, SALTBYTES
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
    def derive_key_from_password(password: str, salt: bytes) -> bytes:
        """Извлекает криптографический ключ из обычного пароля (Argon2id)."""
        return kdf(
            SecretBox.KEY_SIZE,
            password.encode("utf-8"),
            salt,
            opslimit=OPSLIMIT_MODERATE,
            memlimit=MEMLIMIT_MODERATE,
        )

    def encrypt_private_key(self, password: str) -> Tuple[bytes, bytes, bytes]:
        """Шифрует приватный ключ и подпись-ключ мастер-паролем."""
        salt = nacl.utils.random(SALTBYTES)
        key = self.derive_key_from_password(password, salt)
        box = SecretBox(key)
        nonce = nacl.utils.random(SecretBox.NONCE_SIZE)
        encrypted = box.encrypt(self.private_key_bytes, nonce)

        return encrypted.ciphertext, salt, nonce

    @classmethod
    def decrypt_private_key(
        cls, encrypted_private_key: bytes, password: str, salt: bytes, nonce: bytes
    ):
        """Делает приватный ключ и подпись-ключ из зашифрованных данных и возвращает объект CryptoManager."""

        key = cls.derive_key_from_password(password, salt)
        box = SecretBox(key)

        try:
            priv_bytes = box.decrypt(encrypted_private_key, nonce)
            return cls(private_key_bytes=priv_bytes)
        except Exception:
            raise ValueError("Неверный пароль или поврежденные данные!")

    def sign_ciphertext(self, ciphertext: bytes) -> bytes:
        """Создает цифровую подпись для сообщения."""
        signing_key = SigningKey(self.private_key_bytes)
        return signing_key.sign(ciphertext).signature

    @staticmethod
    def verify_message(self, message: str, signature: str):
        """Проверяет подпись сообщения и возвращает результат проверки."""
        verkey = VerifyKey(self.public_key_bytes)
        return verkey.verify(message, signature, encoder=HexEncoder)

    def get_encrypted_file_and_file_key(self, file_path: str):
        file_key = nacl.utils.random(SecretBox.KEY_SIZE)
        box = SecretBox(file_key)

        with open(file_path, "rb") as f:
            encrypted_file = box.encrypt(f.read())
        return encrypted_file, file_key

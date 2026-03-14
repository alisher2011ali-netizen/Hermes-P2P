from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Column,
    String,
    LargeBinary,
    ForeignKey,
    DateTime,
    Boolean,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Identity(Base):
    """Хранение собственных ключей и локального профиля."""

    __tablename__ = "identity"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(50))
    public_key: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    private_key_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    key_salt: Mapped[bytes] = mapped_column(LargeBinary)
    key_nonce: Mapped[bytes] = mapped_column(LargeBinary)
    tor_private_key: Mapped[str] = mapped_column(String(100), nullable=True)
    onion_address: Mapped[str] = mapped_column(String(100), nullable=True)


class Contact(Base):
    """Список контактов (друзей) и их публичные ключи."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    alias: Mapped[str] = mapped_column(String(100))
    public_key: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    onion_address: Mapped[str] = mapped_column(String(100), nullable=False)
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="contact")


class Message(Base):
    """Архив переписки."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE")
    )
    is_outbox: Mapped[bool] = mapped_column(Boolean)
    encrypted_content: Mapped[bytes] = mapped_column(LargeBinary)
    nonce: Mapped[bytes] = mapped_column(LargeBinary)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False)

    contact = relationship("Contact", back_populates="messages")


class ProxySettings(Base):
    """Настройки Tor и мостов."""

    __tablename__ = "proxy_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    proxy_type: Mapped[str] = mapped_column(String(20), default="sock5")
    host: Mapped[str] = mapped_column(String(100), default="127.0.0.1")
    port: Mapped[int] = mapped_column(BigInteger, default="9050")

    bridge_config: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

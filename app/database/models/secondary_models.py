from datetime import datetime
from sqlalchemy import (
    String,
    LargeBinary,
    ForeignKey,
    DateTime,
    Boolean,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Identity(Base):
    """Хранение собственных ключей и локального профиля."""

    __tablename__ = "identity"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), onupdate="CASCADE", unique=True)
    bio: Mapped[str] = mapped_column(String(200), nullable=True)
    public_key: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    encrypted_private_key: Mapped[bytes] = mapped_column(LargeBinary)
    key_salt: Mapped[bytes] = mapped_column(LargeBinary)
    key_nonce: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Contact(Base):
    """Список контактов (друзей) и их публичные ключи."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    bio: Mapped[str] = mapped_column(String(200), nullable=True)
    public_key: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now
    )
    last_message_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")

    messages = relationship("Message", back_populates="contact")


class Message(Base):
    """Архив переписки."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE")
    )
    type_content: Mapped[str] = mapped_column(String, default="TEXT")
    encrypted_text: Mapped[bytes] = mapped_column(LargeBinary)
    nonce: Mapped[bytes] = mapped_column(LargeBinary)
    signature: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_outbox: Mapped[bool] = mapped_column(Boolean)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    error_log: Mapped[str] = mapped_column(Text, nullable=True)

    contact = relationship("Contact", back_populates="messages")

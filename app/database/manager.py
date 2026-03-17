import os
from typing import Tuple
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database.models import Base, Message, Identity, Contact
from app.core.crypto import CryptoManager

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://hermes:alisher2011%@localhost:5432/hermes_db",
)


class DBManager:
    def __init__(self):
        self.engine = create_async_engine(
            DATABASE_URL,
            echo=True,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine, expire_on_commit=False
        )

    async def init_db(self):
        """Эта функция создает таблицы, если их еще нет."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("--- База данных инициализирована, таблицы созданы! ---")

    async def get_session(self) -> AsyncSession:  # type: ignore
        async with self.session_factory() as session:
            yield session

    async def save_message(
        self,
        contact_id: int,
        encrypted_content: bytes,
        nonce: bytes,
        signature_bytes: bytes,
        is_outbox: bool,
    ):
        """Сохраняет зашифрованное сообщение."""
        async with self.session_factory() as session:
            async with session.begin():
                new_msg = Message(
                    encypted_content=encrypted_content,
                    nonce=nonce,
                    signature=signature_bytes,
                    contact_id=contact_id,
                    is_outbox=is_outbox,
                )
                session.add(new_msg)
                await session.commit()
                return new_msg

    async def create_new_identity(
        self, name: str, password: str
    ) -> Tuple[Identity, CryptoManager]:
        crypto = CryptoManager()

        encrypted_keys, salt, nonce = crypto.encrypt_all_keys(password)

        async with self.session_factory() as session:
            async with session.begin():
                identity = Identity(
                    display_name=name,
                    public_key=crypto.public_key_bytes,
                    verify_key=crypto.verify_key_bytes,
                    encrypted_keys=encrypted_keys,
                    key_salt=salt,
                    key_nonce=nonce,
                )
                session.add(identity)
                await session.commit()
                print(f"[DB] Профиль {name} создан!")
                return identity, crypto

    async def get_all_identities(self) -> list[Identity]:
        """Возвращает список всех созданных профилей."""
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(sa.select(Identity))
                return result.scalars().all()

    async def get_identity_by_name(self, name: str):
        """Находит профиль по имени."""
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    sa.select(Identity).filter_by(display_name=name)
                )
                identity = result.scalars().first()
                return identity

    async def unlock_identity(
        self, target_name: str, password: str
    ) -> Tuple[Identity, CryptoManager]:
        """Проверяет пароль и возвращает объект Identity, объект CryptoManager."""
        async with self.session_factory() as session:
            result = await session.execute(
                sa.select(Identity).filter_by(display_name=target_name)
            )
            identity = result.scalars().first()

            if not identity:
                print("Профиль не найден! Сначала создай его.")
                return None

            crypto = CryptoManager.decrypt_all_keys(
                encrypted_blob=identity.encrypted_keys,
                password=password,
                salt=identity.key_salt,
                nonce=identity.key_nonce,
            )

            if crypto:
                print(f"Добро пожаловать, {identity.display_name}!")
                return identity, crypto
            else:
                print("Неверный мастер-пароль!")
                return None

    async def add_contact(
        self, alias: str, pub_key: bytes, verify_key: bytes, onion_address: str
    ) -> Contact:
        async with self.session_factory() as session:
            async with session.begin():
                contact = Contact(
                    alias=alias,
                    public_key=pub_key,
                    verify_key=verify_key,
                    onion_address=onion_address,
                )
                session.add(contact)
                await session.commit()
                print(f"[DB] Контакт {alias} создан!")
                return contact

    async def save_tor_data(
        self, name: str, tor_private_key: str, onion_address: str
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                query = (
                    sa.update(Identity)
                    .where(Identity.display_name == name)
                    .values(
                        tor_private_key=tor_private_key, onion_address=onion_address
                    )
                )

                result = await session.execute(query)

                if result.rowcount == 0:
                    print(f"[DB] Ошибка: Пользователь с именем {name} не найден.")
                else:
                    print(f"[DB] Tor-ключ и Onion-адрес успешно сохранены для {name}.")

    async def get_all_contacts_for_once(self, name: str) -> list[Contact]:
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    sa.select(Contact).filter_by(profile=name)
                )
                contacts = result.scalars().all()

                return contacts

    async def get_contact_by_id(self, contact_id: int) -> Contact:
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    sa.select(Contact).filter_by(id=contact_id)
                )
                contact = result.scalars().first()

                return contact

    async def get_contact_by_onion(self, onion: int) -> Contact:
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    sa.select(Contact).filter_by(onion_address=onion)
                )
                contact = result.scalars().first()

                return contact

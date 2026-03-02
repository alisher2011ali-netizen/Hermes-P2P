import os
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from database.models import Base, Message, Identity, Contact
from core.crypto import CryptoManager

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
        self, contact_id: int, is_outbox: bool, content: bytes, nonce: bytes
    ):
        """Сохраняет зашифрованное сообщение."""
        async with self.session_factory() as session:
            async with session.begin():
                new_msg = Message(
                    contact_id=contact_id,
                    is_outbox=is_outbox,
                    encrypted_content=content,
                    nonce=nonce,
                )
                session.add(new_msg)
                await session.commit()
                return new_msg

    async def get_or_create_identity(self, name: str):
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(sa.select(Identity))
                identity = result.scalars().first()

                if not identity:
                    print("[DB] Создаю новый профиль пользователя...")
                    crypto = CryptoManager()

                    identity = Identity(
                        display_name=name,
                        public_key=crypto.public_key_bytes,
                        private_key_encrypted=crypto.private_key_bytes,
                    )
                    session.add(identity)
                    await session.commit()
                    print(f"[DB] Профиль {name} создан!")

                return identity

    async def get_or_create_contact(
        self, id: int, alias: str, public_key: bytes, onion_address: str
    ):
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(sa.select(Contact))
                contact = result.scalars().first()

                if not contact:
                    print("[DB] Создаю новый контакт пользователя...")

                    contact = Contact(
                        id=id,
                        alias=alias,
                        public_key=public_key,
                        onion_address=onion_address,
                    )
                    session.add(contact)
                    await session.commit()
                    print(f"[DB] Контакт {alias} создан!")
                return contact

    async def unlock_identity(self, password: str):
        """Проверяет пароль и возвращает объект CryptoManager."""
        async with self.session_factory() as session:
            result = await session.execute(sa.select(Identity))
            identity = result.scalars().first()

            if not identity:
                print("Профиль не найден! Сначала создай его.")
                return None

            crypto = CryptoManager.decrypt_private_key(
                encrypted_key=identity.private_key_encrypted,
                password=password,
                salt=identity.key_salt,
                nonce=identity.key_nonce,
            )

            if crypto:
                print(f"Добро пожаловать, {identity.display_name}!")
                return crypto
            else:
                print("Неверный мастер-пароль!")
                return None

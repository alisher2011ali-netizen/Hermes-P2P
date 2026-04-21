from sqlalchemy import select
import os

from app.database.manager import (
    get_session_factory,
    main_session_factory,
    init_profile_db,
)
from app.database.models.main_models import Account
from app.database.models.secondary_models import Identity
from app.database.repositories import identity as identity_repo
from app.database.repositories import accounts
from app.core.crypto import CryptoManager
from app.state import state


class AuthService:
    def __init__(self):
        self.main_session = main_session_factory

    async def login(self, name: str, password: str):
        async with self.main_session() as session:
            account = await accounts.get_account_by_name(session=session, name=name)
            db_path = account.db_file_path

        profile_session_factory = get_session_factory(db_path)
        state.session_factory = profile_session_factory

        async with profile_session_factory() as profile_session:
            identity: Identity = await identity_repo.get_identity_by_name(
                session=profile_session, name=name
            )

            if not identity:
                raise ValueError("Профиль не найден!")

            try:
                crypto = CryptoManager.decrypt_private_key(
                    encrypted_private_key=identity.encrypted_private_key,
                    password=password,
                    salt=identity.key_salt,
                    nonce=identity.key_nonce,
                )
            except Exception:
                raise ValueError("Неверный мастер-пароль!")

        state.crypto = crypto
        state.current_account = identity
        state.session_factory = profile_session_factory
        return True

    async def sign_up(self, name: str, password: str):
        user_dir = f"./data/{name}"
        os.makedirs(user_dir, exist_ok=True)

        async with self.main_session() as session:
            account = Account(display_name=name, db_file_path=f"{user_dir}/{name}.db")
            session.add(account)

            await init_profile_db(account.db_file_path)
            profile_session_factory = get_session_factory(db_path=account.db_file_path)
            state.session_factory = profile_session_factory
            async with profile_session_factory() as profile_session:
                crypto = CryptoManager()

                encrypted_private_key, salt, nonce = crypto.encrypt_private_key(
                    password
                )

                identity = Identity(
                    name=name,
                    public_key=crypto.public_key_bytes,
                    encrypted_private_key=encrypted_private_key,
                    key_salt=salt,
                    key_nonce=nonce,
                )
                profile_session.add(identity)

                await profile_session.commit()
            await session.commit()

        state.crypto = crypto
        state.current_account = identity

        return True

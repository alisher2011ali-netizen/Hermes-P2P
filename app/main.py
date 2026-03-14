import asyncio

from app.database.manager import DBManager
from app.services.auth import AuthService
from app.network.tor_manager import TorManager


async def main():
    db = DBManager()
    while True:
        try:
            await db.init_db()
            break
        except Exception as e:
            print(e)

    auth = AuthService(db)
    identity, crypto = await auth.run_auth_flow()

    if not crypto:
        print("Авторизация не удалась. Выход.")
        return

    print(
        f"Система готова. Ваш публичный ключ: {crypto.public_key_bytes.hex()[:16]}..."
    )

    tor = TorManager(host="tor")
    await tor.connect()
    onion_addr = await tor.setup_identity_tor(name=identity.display_name, db=db)


if __name__ == "__main__":
    asyncio.run(main())

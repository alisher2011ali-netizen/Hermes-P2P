import asyncio

from app.database.manager import DBManager
from app.services.auth import AuthService
from app.network.tor_manager import TorManager


async def main():
    db = DBManager()
    await db.init_db()

    auth = AuthService(db)
    crypto = await auth.run_auth_flow()

    if not crypto:
        print("Авторизация не удалась. Выход.")
        return

    print(
        f"Система готова. Ваш публичный ключ: {crypto.public_key_bytes.hex()[:16]}..."
    )

    tor = TorManager(host="tor")
    await tor.connect()
    onion_addr = await tor.create_hidden_service(local_port=8080)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

from app.database.manager import DBManager
from app.services.auth import AuthService
from app.network.tor_manager import TorManager
from app.network.protocol import HermesProtocol
from app.ui.console import CLIInterface


async def main():
    db = DBManager()
    try:
        await db.init_db()
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

    ui = CLIInterface(db=db, identity=identity, crypto=crypto)

    await ui.run()


if __name__ == "__main__":
    asyncio.run(main())

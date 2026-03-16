import asyncio

from app.database.manager import DBManager
from app.services.auth import AuthService
from app.network.tor_manager import TorManager
from app.network.protocol import HermesProtocol
from app.network.p2p_node import P2PNode
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

    node = P2PNode(db=db, crypto=crypto)

    tor = TorManager(host="tor")
    await tor.connect()
    tor_private_key, onion_addr = await tor.setup_identity_tor(identity.tor_private_key)

    if not identity.tor_private_key:
        await db.save_tor_data(
            identity.display_name, tor_private_key, onion_address=onion_addr
        )

    server_task = asyncio.create_task(node.run_server())

    ui = CLIInterface(db=db, identity=identity, crypto=crypto)
    await ui.run()

    server_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())

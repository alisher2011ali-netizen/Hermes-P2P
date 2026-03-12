import asyncio

from app.database.manager import DBManager
from app.services.auth import AuthService


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
    print("Ожидание сетевых событий (Tor)...")


if __name__ == "__main__":
    asyncio.run(main())

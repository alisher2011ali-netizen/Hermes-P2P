import asyncio

from app.core.engine import AppEngine


async def main():
    engine = AppEngine()

    if await engine.setup():
        await engine.run()
    else:
        print("Ошибка запуска приложения.")


if __name__ == "__main__":
    asyncio.run(main())

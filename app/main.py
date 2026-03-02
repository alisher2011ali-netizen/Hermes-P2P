import asyncio

from database.manager import DBManager


async def main():
    db = DBManager()
    await db.init_db()


if __name__ == "__main__":
    asyncio.run(main())

import httpx
import json
import asyncio

from app.state import state


async def send_packet(packet: json):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{state.relay_url}/send", json=packet)

            if response.status_code == 200:
                return True
        except Exception as e:
            raise False


async def pull_messages():
    while True:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{state.relay_url}/inbox/{state.crypto.public_key_bytes.hex()}"
            )

            if response.status_code == 200:
                messages = response.json()
                for msg in messages:
                    # 1. Проверяем подпись (VerifyKey отправителя)
                    # 2. Расшифровываем (decrypt_from)
                    # 3. Сохраняем в БД и обновляем UI
                    pass

        await asyncio.sleep(5)

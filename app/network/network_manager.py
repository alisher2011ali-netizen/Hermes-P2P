import httpx
import asyncio
import logging
import json
from pydantic import BaseModel
from typing import Optional

from app.state import state

logger = logging.getLogger(__name__)


class MessagePacket(BaseModel):
    to_pubkey: str
    from_pubkey: str
    msg_type: str = "TEXT"
    payload: str
    file_id: Optional[str] = None
    nonce: str
    signature: str
    timestamp: str


class NetworkManager:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self._polling_task: Optional[asyncio.Task] = None

    async def send_packet(self, packet: MessagePacket) -> bool:
        """Отправляет пакет на Relay-сервер."""
        if self.client.is_closed:
            self.client = httpx.AsyncClient(timeout=10.0)
        try:
            response = await self.client.post(
                f"{state.relay_url}/send", json=packet.model_dump()
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ошибка при отправке пакета: {e}")
            return False

    async def upload_file(self, encrpted_data: bytes) -> str:
        files = {"file": ("blob", encrpted_data)}
        response = await self.client.post(f"{state.relay_url}/upload", files=files)
        if response.status_code == 200:
            return response.json()["file_id"]
        raise Exception("Failed to upload file")

    async def start_polling(self):
        """Запускает бесконечный цикл опроса сервера."""
        if self._polling_task:
            return

        self._polling_task = asyncio.create_task(self._pull_loop())

    async def _pull_loop(self):
        """Внутренний цикл получения сообщений."""
        while True:
            if not state.crypto:
                await asyncio.sleep(2)
                continue

            try:
                my_pubkey = state.crypto.public_key_bytes.hex()
                response = await self.client.get(f"{state.relay_url}/fetch/{my_pubkey}")

                if response.status_code == 200:
                    raw_packets = response.json()

                    if raw_packets:
                        from app.services.message_service import MessageService

                        for raw_data in raw_packets:
                            packet_data = (
                                json.loads(raw_data)
                                if isinstance(raw_data, str)
                                else raw_data
                            )
                            packet = MessagePacket(**packet_data)

                            await MessageService.polling_message(
                                state.session_factory, packet
                            )
            except Exception as e:
                logging.error(f"Ошибка при опросе сервера: {e}")

            await asyncio.sleep(5)

    async def stop(self):
        """Закрывает клиент при выходе."""
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        await self.client.aclose()


network_manager = NetworkManager()

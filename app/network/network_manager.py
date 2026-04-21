import httpx
import json
from pydantic import BaseModel
import asyncio

from app.state import state
from app.services.message_service import MessageService


class MessagePacket(BaseModel):
    to_pubkey: str
    from_pubkey: str
    payload: str
    nonce: str
    signature: str
    timestamp: str


async def send_packet(packet: MessagePacket):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{state.relay_url}/send", json=packet.model_dump()
            )

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
                packets = response.json()
                for packet in packets:
                    await MessageService.polling_message(packet=packet)
                    pass

        await asyncio.sleep(5)

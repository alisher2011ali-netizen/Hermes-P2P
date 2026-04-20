from fastapi import FastAPI, HTTPException
from typing import List, Dict
import collections

from api.schemas import MessagePacket

app = FastAPI(title="Hermes-Node (Relay)")

mail_storage = collections.defaultdict(list)


@app.get("/status")
async def status():
    return {"status": "online", "message": "Hermes Relay Node is running"}


@app.post("/send")
async def send_messages(packet: MessagePacket):
    """Принимает сообщение и кладет в 'ящик' получателя."""
    if len(mail_storage[packet.to_pubkey]) > 100:
        raise HTTPException(status_code=429, detail="Ящик получателя переполнен")

    mail_storage[packet.to_pubkey].append(packet.model_dump())
    return {"status": "sent", "timestamp": "ok"}


@app.get("/fetch/{pubkey}")
async def fetch_messages(pubkey: str) -> List[MessagePacket]:
    """Отдает сообщения и удаляет их из хранилища."""
    messages = mail_storage.get(pubkey, [])

    if not messages:
        return []

    del mail_storage[pubkey]

    return messages

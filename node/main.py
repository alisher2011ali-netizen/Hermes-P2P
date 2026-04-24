import os
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from sqlalchemy import select, delete

from node.database.models import RelayMessage, async_session
from node.api.schemas import MessagePacket

app = FastAPI(title="Hermes-Node (Relay)")
STORAGE_DIR = Path("node/storage_files")
STORAGE_DIR.mkdir(exist_ok=True)


@app.post("/upload")
async def upload_file(file: UploadFile = File()):
    """Принимает зашифрованный файл и сохраняет его под уникальным ID"""
    file_id = str(uuid.uuid4())
    file_path = STORAGE_DIR / file_id

    with open(file_path, "wb") as buffer:
        while content := await file.read(1024 * 1024):
            buffer.write(content)

    return {"file_id": file_id}


@app.post("/send")
async def send_message(packet: MessagePacket):
    async with async_session() as session:
        new_msg = RelayMessage(
            from_pubkey=packet.from_pubkey,
            to_pubkey=packet.to_pubkey,
            payload=packet.payload,
            file_id=getattr(packet, "file_id", None),
        )
        session.add(new_msg)
        await session.commit()
    return {"status": "stored"}


@app.get("fetch/{pubkey}")
async def fetch_messages(pubkey: str):
    async with async_session() as session:
        result = await session.execute(
            select(RelayMessage).where(RelayMessage.to_pubkey == pubkey)
        )
        messages = result.scalars().all()

        if not messages:
            return []

        await session.execute(
            delete(RelayMessage).where(RelayMessage.to_pubkey == pubkey)
        )
        await session.commint()
        return [msg.payload for msg in messages]


@app.get("/download/file_id")
async def download_file(file_id: str):
    """Отдает зашифрованный файл по его ID."""
    file_path = STORAGE_DIR / file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fiel not found")

    from fastapi.responses import FileResponse

    return FileResponse(path=file_path)

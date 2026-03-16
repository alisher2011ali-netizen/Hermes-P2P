from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import uvicorn

from app.database.manager import DBManager
from app.core.crypto import CryptoManager
from app.services.message_processor import MessageService


class MessagePacket(BaseModel):
    sender_name: str
    sender_onion: str
    ciphertext: str
    nonce: str
    signature: str


class P2PNode:
    def __init__(self, db: DBManager, crypto: CryptoManager):
        self.app = FastAPI()
        self.message_service = MessageService(db, crypto)
        self._setup_routes()

    def _setup_routes(self):
        @self.app.post("/receive")
        async def handle_message(packet: MessagePacket):
            try:
                await self.message_service.process_incoming(packet)
                return {"status": "delivered"}
            except Exception as e:
                raise HTTPException(status_code=400, detail="Decryption failed")

    async def run_server(self):
        config = uvicorn.Config(self.app, host="0.0.0.0", port=8080)
        server = uvicorn.Server(config)
        await server.serve()

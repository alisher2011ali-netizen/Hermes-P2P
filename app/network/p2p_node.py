from fastapi import FastAPI

from app.network.tor_manager import TorManager
from app.database.manager import DBManager


class P2PNode:
    def __init__(self):
        self.app = FastAPI()
        self.tor = TorManager()
        self._setup_routes()

    def _setup_routes(self):
        @self.app.post("/message")
        async def handle_message(data: dict):
            return {"status": "ok"}

    async def start(self, name: str, db: DBManager):
        onion = await self.tor.setup_identity_tor(name, db)

import asyncio

from app.database.manager import DBManager
from app.network.tor_manager import TorManager
from app.network.p2p_node import P2PNode
from app.services.auth import AuthService
from app.ui.console import CLIInterface


class AppEngine:
    def __init__(self):
        self.db = DBManager()
        self.auuth = None
        self.crypto = None
        self.identity = None
        self.tor = TorManager(host="tor")
        self.node = None

    async def setup(self):
        """Вся работа по инициализации здесь"""
        await self.db.init_db()
        self.auth = AuthService(self.db)

        self.identity, self.crypto = await self.auth.run_auth_flow()
        if not self.crypto:
            return False

        await self.tor.connect()
        self.node = P2PNode(db=self.db, crypto=self.crypto)
        return True

    async def run(self):
        """Запуск всех фоновых задач и UI"""
        server_task = asyncio.create_task(self.node.run_server())

        ui = CLIInterface(db=self.db, identity=self.identity, crypto=self.crypto)
        await ui.run()

        server_task.cancel()

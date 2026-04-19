from pathlib import Path

from app.database.manager import init_main_db
from app.state import state


class AppEngine:
    def __init__(self):
        self.node = None
        self.running_tasks = None

    async def initialize_system(self):
        """Глобальная инициализация при старте программы (до входа)"""
        data = Path("./data")
        if not data.exists():
            data.mkdir(parents=True, exist_ok=True)
        await init_main_db()
        print("[Engine] Global system initialized.")

    async def start_services(self):
        """Запуск фоновых служб ПОСЛЕ авторизации"""
        if not state.is_authenticated:
            print("[Engine] Error: Cannot start services without authentication.")
            return

        print(f"[Engine] Starting services for {state.current_account.name}...")

        # Здесь будет запуск Relay-клиента или P2P ноды
        # self.node = RelayClient(crypto=state.crypto)
        # task = asyncio.create_task(self.node.run())
        # self.running_tasks.append(task)

        print("[Engine] All services are online.")

    async def stop_services(self):
        """Чистая остановка всех задач"""
        for task in self.running_tasks:
            task.cancel()

        state.clear()
        print("[Engine] Services stopped and state cleared.")

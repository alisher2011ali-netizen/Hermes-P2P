import asyncio
import socket
from stem.control import Controller
from stem import Signal
import os

from app.database.manager import DBManager


class TorManager:
    def __init__(self, control_port=9051, host="tor"):
        self.port = control_port
        self.host = host
        self.controller = None
        self.onion_address = None

    async def connect(self):
        """Подключаемся к контрольному порту Tor."""
        password = os.getenv("TOR_PASSWORD")

        while True:
            try:
                target_ip = socket.gethostbyname(self.host)

                with socket.create_connection((target_ip, self.port), timeout=2):
                    self.controller = Controller.from_port(
                        address=target_ip, port=self.port
                    )
                    self.controller.authenticate(password=password)
                    print(f"[Tor] Успешно подключено к {target_ip}:{self.port}")
                    break
            except (socket.gaierror, ConnectionRefusedError, OSError):
                print("[Tor] Порт закрыт. Tor еще загружается... Ждем 5 сек.")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[Tor] Ожидание запуска Tor... ({e})")
                await asyncio.sleep(2)

    async def setup_identity_tor(self, name: str, db: DBManager):
        response = self.controller.create_ephemeral_hidden_service(
            {80: 8080}, detached=True
        )

        new_private_key = response.private_key
        new_onion_address = f"{response.service_id}.onion"

        await db.save_tor_private_key(name, new_private_key)

        return new_onion_address

    async def create_permanent_onion(self, stored_key: str):
        """
        Создает ПОСТОЯННЫЙ адрес на основе твоего ключа.
        """
        try:
            response = self.controller.create_ephemeral_hidden_service(
                {80: 8080}, key_content=stored_key, detached=True
            )
            return f"{response.service_id}.onion"
        except Exception as e:
            print(f"[Tor] Ошибка запуска с ключом: {e}")

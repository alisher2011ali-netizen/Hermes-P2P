import asyncio
import socket
from stem.control import Controller
from stem import Signal


class TorManager:
    def __init__(self, control_port=9051, host="tor"):
        self.port = control_port
        self.host = host
        self.controller = None
        self.onion_addresss = None

    async def connect(self):
        """Подключаемся к контрольному порту Tor."""
        while True:
            try:
                target_ip = socket.gethostbyname(self.host)

                with socket.create_connection((target_ip, self.port), timeout=2):
                    self.controller = Controller.from_port(
                        address=target_ip, port=self.port
                    )
                    self.controller.authenticate()
                    print(f"[Tor] Успешно подключено к {target_ip}:{self.port}")
                    break
            except (socket.gaierror, ConnectionRefusedError, OSError):
                print("[Tor] Порт закрыт. Tor еще загружается... Ждем 5 сек.")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[Tor] Ожидание запуска Tor... ({e})")
                await asyncio.sleep(2)

    async def create_hidden_service(self, local_port=8080):
        """Создает эфемерный (временный) .onion адрес."""
        if not self.controller:
            await self.connect()

        response = self.controller.create_ephemeral_hidden_service(
            {80: local_port}, await_managed=True
        )
        self.onion_addresss = f"{response.service_id}.onion"

        print(f"[Tor] Ваш адрес в сети: {self.onion_address}")
        return self.onion_addresss

    async def create_permanent_onion(self, private_key_bytes: bytes):
        """
        Создает ПОСТОЯННЫЙ адрес на основе твоего ключа.
        """

        response = self.controller.create_ephemeral_hidden_service(
            {80: 8080}, await_managed=True
        )
        return f"{response.service_id}.onion"

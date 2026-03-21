import asyncio
import socket
from stem.control import Controller
from stem import Signal
import os
from typing import Tuple, List


class TorManager:
    def __init__(self, control_port=9051, host="tor"):
        self.port = control_port
        self.host = host
        self.controller = None
        self.private_key = None
        self.onion_address = None

    async def connect(self) -> None:
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

    async def setup_identity_tor(
        self, stored_key: str = None
    ) -> Tuple[bytes, str] | str:
        """
        Создает onion-адрес на основе ключа, если он есть. В противном случае создается новый ключ.
        """
        try:
            if stored_key:
                response = self.controller.create_ephemeral_hidden_service(
                    {80: 8080}, key_content=stored_key, detached=True
                )
                return f"{response.service_id}.onion"

            response = self.controller.create_ephemeral_hidden_service(
                {80: 8080}, detached=True
            )

            self.private_key = response.private_key
            self.onion_address = f"{response.service_id}.onion"

            return self.private_key, self.onion_address
        except Exception as e:
            print(f"[Tor] Ошибка запуска с ключом: {e}")

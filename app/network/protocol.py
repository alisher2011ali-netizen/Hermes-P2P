import httpx


class HermesProtocol:
    def __init__(self, tor_proxy="socks5://tor:9050"):
        self.proxy = tor_proxy

    async def send_payload(self, target_onion: str, json: dict):
        """Отправляет данные на чужой .onion адрес"""

        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        async with httpx.AsyncClient(
            proxy=self.proxy, limits=limits, timeout=30.0
        ) as client:
            url = f"http://{target_onion}/receive_message"
            try:
                response = await client.post(url, json=json)

                if response.status_code == 200:
                    print(f"[+] Сообщение для {target_onion} успешно отправлено")
                    return True
                else:
                    print(f"[-] Ошибка узла: {response.status_code}")
                    return False
            except httpx.RequestError as exc:
                print(f"[-] Не удалось связаться с узлом {target_onion}: {exc}")
                return False

import httpx


class HermesProtocol:
    def __init__(self, tor_proxy="socks5://tor:9050"):
        self.proxy = tor_proxy

    async def send_payload(
        self, target_onion: str, payload: dict, signing_key_hex: str
    ):
        """Отправляет данные на чужой .onion адрес"""
        pass

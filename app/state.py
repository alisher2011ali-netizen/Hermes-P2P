from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.crypto import CryptoManager
from app.database.models import Identity, Contact


class AppState:
    current_account: Identity = None
    crypto: CryptoManager = None
    session_factory: async_sessionmaker = None
    relay_url: str = "http://127.0.0.1:8000"

    def clear(self):
        """Полная очистка при выходе (Log out)"""
        self.current_account = None
        self.crypto = None
        self.session_factory = None
        self.current_page = "login"

    @property
    def is_authenticated(self) -> bool:
        return self.current_account is not None and self.crypto is not None

    def sort_contacts(self):
        """Сортирует контакты так, чтобы активные были сверху."""
        self.contacts_list.sort(key=lambda x: x.last_message_time, reverse=True)

    def update_contact_pos(self, contact_id: int):
        """Находит контакт и перемещает его в начало списка (пришло сообщение)."""
        for i, c in enumerate(self.contacts_list):
            if c.id == contact_id:
                target = self.contacts_list.pop(i)
                self.contacts_list.insert(0, target)
                break


state = AppState()

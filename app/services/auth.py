from app.database.manager import DBManager
from app.core.crypto import CryptoManager
import getpass


class AuthService:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    async def run_auth_flow(self):
        """Главный цикл выбора: вход или регистрация."""
        print("\n--- HERMES P2P AUTHENTICATION ---")

        users = await self.db.get_all_identities()

        if not users:
            return await self._register_flow()

        print("1. Войти")
        print("2. Создать новый профиль")
        choice = input("Выберите действие: ")

        if choice == "1":
            return await self._login_flow(users)
        else:
            return await self._register_flow()

    async def _register_flow(self):
        print("\n[Регистрация нового профиля]")
        name = input("Введите имя: ")
        password = getpass.getpass("Придумайте мастер-пароль: ")

        result = await self.db.create_new_identity(name, password)
        return result

    async def _login_flow(self, users):
        print("\n[Вход в систему]")
        for i, user in enumerate(users, 1):
            print(f"{i}. {user.display_name}")

        target_name = input("Имя пользователя: ")
        password = getpass.getpass(f"Пароль для {target_name}: ")

        result = await self.db.unlock_identity(target_name, password)
        return result

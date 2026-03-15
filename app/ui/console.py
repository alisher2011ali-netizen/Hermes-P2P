from app.database.manager import DBManager
from app.database.models import Identity
from app.core.crypto import CryptoManager
from app.utils.re_validation import *


class CLIInterface:
    def __init__(self, db: DBManager, identity: Identity, crypto: CryptoManager):
        self.db = db
        self.identity = identity
        self.crypto = crypto
        self.current_state = "CHAT_LIST"

    async def run(self):
        while True:
            if self.current_state == "CHAT_LIST":
                await self.show_chat_list()
            elif self.current_state == "ADD_CONTACT":
                await self.show_add_contact()
            elif self.current_state == "EXIT":
                break

    async def show_chat_list(self):
        contacts = await self.db.get_all_contacts_for_once(self.identity.display_name)
        if not contacts:
            print("У вас нет контактов. Перейти к созданию (Y/n)?")
            confirm = input("\n> ")
            if confirm == "Y" or confirm == "y":
                self.current_state = "ADD_CONTACT"
                return
        print("\n--- ВАШИ КОНТАКТЫ ---")
        for idx, c in enumerate(contacts):
            print(f"ID: {idx}. {c.alias} ({c.onion_address})")
        print("\nКоманды: [id] - открыть чат, 'add' - новый контакт, 'exit' - выход")
        choice = input("\n> ")
        if choice == "exit":
            self.current_state = "EXIT"
        elif choice == "add":
            self.current_state == "ADD_CONTACT"

    async def show_add_contact(self):
        c_alias = input("Вы перешли к созданию контакта.\nВведите имя контакта.\n> ")
        c_onion = input("Введите Onion-адрес контакта/\n> ")

        if not is_valid_onion(c_onion):
            print("Неверный Onion-адрес. Попробуте заново.")
            return

        c_pub_key = input("Введите публичный ключ контакта.\n> ")
        c_verify_key = input("Введите ключ верификации контакта.\n> ")
        confirm = input(
            f"Вы уверены, что хотет создать контакт с данными:\n"
            f"Имя: {c_alias}\n"
            f"Onion-адрес: {c_onion}\n"
            f"Публичный ключ: {c_pub_key}\n"
            f"Ключ верификации: {c_verify_key}\n"
            "(Y/n)\n"
            "> "
        )
        if confirm == "Y" or confirm == "y":
            await self.db.add_contact(
                alias=c_alias,
                pub_key=bytes.fromhex(c_pub_key),
                verify_key=bytes.fromhex(c_verify_key),
                onion_address=c_onion,
            )
            print("Контакт умпешно создан!")
        current_state = "CHAT_LIST"

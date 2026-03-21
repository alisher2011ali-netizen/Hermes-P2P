from datetime import datetime

from app.database.manager import DBManager
from app.database.models import Identity
from app.core.crypto import CryptoManager
from app.services.message_processor import MessagePacket, MessageService
from app.utils.re_validation import *


class CLIInterface:
    def __init__(self, db: DBManager, identity: Identity, crypto: CryptoManager):
        self.db = db
        self.identity = identity
        self.crypto = crypto
        self.msg_services = MessageService(db, crypto)
        self.current_chat_id = None
        self.current_state = "CHAT_LIST"
        self.active_contacts = []
        self.contact_to_send = None
        self.message_to_send = None

    async def run(self):
        while True:
            try:
                match self.current_state:
                    case "CHAT_LIST":
                        await self.show_chat_list()
                    case "ADD_CONTACT":
                        await self.show_add_contact()
                    case str(s) if s.isdigit():
                        await self.show_contact_chat()
                    case "SEND_MSG":
                        await self.send_message()
                    case "EXIT":
                        break
            except Exception as e:
                print(f"{e}")
                import traceback

                traceback.print_exc()

    async def show_chat_list(self):
        self.active_contacts = await self.db.get_all_contacts_for_once(
            self.identity.display_name
        )

        print("\n--- ВАШИ КОНТАКТЫ ---")
        if not self.active_contacts:
            print("У вас нет контактов. Перейти к созданию (Y/n)?")
            confirm = input("\n> ")
            if confirm.strip().lower() == "y":
                self.current_state = "ADD_CONTACT"
            return

        for idx, c in enumerate(self.active_contacts):
            print(f"[{idx}] {c.alias} ({c.onion_address})")

        print("\nКоманды: [id] - открыть чат, '/add' - новый контакт, '/exit' - выход")
        choice = input("\n> ").strip()
        match choice:
            case "/exit":
                self.current_state = "EXIT"
            case "/add":
                self.current_state = "ADD_CONTACT"
            case str(s) if s.isdigit():
                if int(choice) >= len(self.active_contacts):
                    print("Неверный номер контакта.")
                    self.current_state = "CHAT_LIST"
                    return
                self.current_state = choice
                self.current_chat_id = self.active_contacts[int(choice)].id

    async def show_add_contact(self):
        c_alias = input("Вы перешли к созданию контакта.\nВведите имя контакта.\n> ")
        c_onion = input("Введите Onion-адрес контакта/\n> ")

        if not is_valid_onion(c_onion):
            print("Неверный Onion-адрес. Попробуте заново.")
            return

        c_pub_key = input("Введите публичный ключ контакта (hex).\n> ")
        c_verify_key = input("Введите ключ верификации контакта (hex).\n> ")
        confirm = input(
            f"Вы уверены, что хотите создать контакт с данными:\n"
            f"Имя: {c_alias}\n"
            f"Onion-адрес: {c_onion}\n"
            f"Публичный ключ: {c_pub_key}\n"
            f"Ключ верификации: {c_verify_key}\n"
            "(Y/n)?\n"
            "> "
        )
        if confirm.strip().lower() == "y":
            try:
                await self.db.add_contact(
                    profile=self.identity.display_name,
                    alias=c_alias,
                    pub_key=bytes.fromhex(c_pub_key),
                    verify_key=bytes.fromhex(c_verify_key),
                    onion_address=c_onion,
                )
                print("Контакт успешно создан!")
            except Exception as e:
                import traceback

                print(f"Ошибка БД: {e}")
                traceback.print_exc()
                self.current_state = "CHAT_LIST"
                return
        else:
            print("Отмена.")
        self.current_state = "CHAT_LIST"

    async def show_contact_chat(self):
        contact = await self.db.get_contact_by_id(int(self.current_chat_id))
        if not contact:
            print("Контакта с таким ID не существует.\n")
            self.current_state = "CHAT_LIST"
            return

        print(f"\n--- ЧАТ С {contact.alias} (Введите '/back' для выхода) ---")

        messages = await self.db.get_messages_by_contact_id(
            self.identity.display_name, int(contact.id)
        )

        for msg in messages:
            try:
                text = self.crypto.decrypt_from(
                    contact.public_key, msg.encrypted_content, msg.nonce
                )
                prefix = "ВЫ" if msg.is_outbox else contact.alias
                print(f"[{prefix}]: {text}")
            except:
                print(f"[{contact.alias}]: <Ошибка расшифровки>")
        msg_input = input("Сообщение > ").strip()

        if msg_input == "/back":
            self.current_state = "CHAT_LIST"
        elif msg_input:
            self.contact_to_send = contact
            self.message_to_send = msg_input
            self.current_state = "SEND_MSG"

    async def send_message(self):
        try:
            ciphertext, nonce = self.crypto.encrypt_for(
                self.contact_to_send.public_key, self.message_to_send
            )
            signature = self.crypto.sign_message(ciphertext.hex())
        except Exception as e:
            import traceback

            print(f"Ошибка БД: {e}")
            traceback.print_exc()
            self.current_state = "CHAT_LIST"
            return

        packet = MessagePacket(
            sender_onion=self.identity.onion_address,
            ciphertext=ciphertext.hex(),
            nonce=nonce.hex(),
            signature=signature.hex(),
            timestamp=datetime.now().isoformat(),
        )
        print("Я здесь: начинаю отправку")
        await self.msg_services.process_outgoing(
            target_onion=self.contact_to_send.onion_address, packet=packet
        )

        print("Сообщение отправлено!")
        self.current_state = self.current_chat_id

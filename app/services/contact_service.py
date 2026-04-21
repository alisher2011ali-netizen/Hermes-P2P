import base58

from app.database.models.secondary_models import Contact
from app.database.repositories import contacts
from app.state import state


async def make_new_contact(name: str, token_string: str):
    try:
        token = token_string.split(":")[1]
        pub_key = base58.b58decode_check(token)

        contact = Contact(name=name, public_key=pub_key)
        async with state.session_factory() as session:
            await contacts.add_contact(session=session, contact=contact)
        return True, None
    except Exception:
        return False, f"Ошибка: Неверный формат ключа или данные повреждены."

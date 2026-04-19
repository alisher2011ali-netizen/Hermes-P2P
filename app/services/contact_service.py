import base58

from app.database.models.secondary_models import Contact
from app.database.repositories import contacts
from app.state import state


async def make_new_contact(name: str, token_string: str):
    try:
        token = token_string.split(":")[1]
        combined = base58.b58decode_check(token)

        pub_key = combined[:32]
        ver_key = combined[32:]

        contact = Contact(name=name, public_key=pub_key, verify_key=ver_key)
        async with state.session_factory() as session:
            await contacts.add_contact(session=session, contact=contact)
        return True, None
    except Exception:
        return False, f"Ошибка: Неверный формат ключа или данные повреждены."

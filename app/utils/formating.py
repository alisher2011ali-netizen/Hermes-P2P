import base58


def generate_invite_token(public_key: bytes) -> str:
    token = base58.b58encode_check(public_key).decode("utf-8")
    return f"TOKEN:{token}"

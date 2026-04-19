import base58


def generate_invite_token(public_key: bytes, verify_key: bytes) -> str:
    combined = public_key + verify_key
    token = base58.b58encode_check(combined).decode("utf-8")
    return f"TOKEN:{token}"

import re


def is_valid_onion(address: str) -> bool:
    pattern = r"^[a-z2-7]{56}\.onion$"
    return bool(re.match(pattern, address.lower()))

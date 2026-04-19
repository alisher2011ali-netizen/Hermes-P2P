import re


def is_valid_pass(password: str):
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    if not re.fullmatch(pattern, password):
        raise ValueError("Неверный формат пароля")
    return True

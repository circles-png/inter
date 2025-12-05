import secrets


def generate_secure_random_string() -> str:
    return secrets.token_urlsafe(32)

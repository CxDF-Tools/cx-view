from cryptography.fernet import InvalidToken

from app.security.keystore import get_fernet


class DecryptionError(Exception):
    pass


def encrypt_str(plaintext: str | None) -> str | None:
    if plaintext is None:
        return None
    return get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_str(ciphertext: str | None) -> str | None:
    if ciphertext is None:
        return None
    try:
        return get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise DecryptionError("Could not decrypt stored credential") from exc

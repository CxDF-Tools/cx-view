import os
from pathlib import Path

from cryptography.fernet import Fernet


def _load_or_create_key(path: Path) -> bytes:
    if path.exists():
        return path.read_bytes()
    key = Fernet.generate_key()
    path.write_bytes(key)
    os.chmod(path, 0o600)
    return key


_fernet: Fernet | None = None


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        from app.config import FERNET_KEY_PATH

        _fernet = Fernet(_load_or_create_key(FERNET_KEY_PATH))
    return _fernet


_session_secret: str | None = None


def get_session_secret() -> str:
    global _session_secret
    if _session_secret is None:
        from app.config import SESSION_KEY_PATH

        _session_secret = _load_or_create_key(SESSION_KEY_PATH).decode()
    return _session_secret

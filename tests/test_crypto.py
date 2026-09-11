import os

from app.security import crypto


def test_encrypt_decrypt_round_trip(tmp_path, monkeypatch):
    key_path = tmp_path / "secret.key"
    monkeypatch.setattr("app.config.FERNET_KEY_PATH", key_path)
    monkeypatch.setattr("app.security.keystore._fernet", None)

    ciphertext = crypto.encrypt_str("super-secret-value")
    assert ciphertext != "super-secret-value"
    assert crypto.decrypt_str(ciphertext) == "super-secret-value"


def test_key_file_has_restrictive_permissions(tmp_path, monkeypatch):
    key_path = tmp_path / "secret.key"
    monkeypatch.setattr("app.config.FERNET_KEY_PATH", key_path)
    monkeypatch.setattr("app.security.keystore._fernet", None)

    crypto.encrypt_str("anything")
    mode = oct(os.stat(key_path).st_mode)[-3:]
    assert mode == "600"


def test_none_passthrough():
    assert crypto.encrypt_str(None) is None
    assert crypto.decrypt_str(None) is None

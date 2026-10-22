import json

import pytest
from cryptography.fernet import Fernet

from whoop_mcp.storage import Store


def test_encrypted_atomic_roundtrip_and_rollback(tmp_path):
    cipher = Fernet(Fernet.generate_key())
    store = Store(tmp_path, cipher)
    with store.transaction() as state:
        state["token"] = "PRIVATE-SECRET"
    raw = (tmp_path / "state.enc").read_bytes()
    assert b"PRIVATE-SECRET" not in raw
    assert json.loads(cipher.decrypt(raw))["token"] == "PRIVATE-SECRET"
    with pytest.raises(ValueError), store.transaction() as state:
        state["token"] = "bad"
        raise ValueError("rollback")
    with store.transaction() as state:
        assert state["token"] == "PRIVATE-SECRET"


def test_untrusted_keyring_refused(tmp_path, monkeypatch):
    import keyring

    monkeypatch.setattr(keyring, "get_keyring", lambda: object())
    with pytest.raises(RuntimeError, match="required"):
        Store(tmp_path).cipher()

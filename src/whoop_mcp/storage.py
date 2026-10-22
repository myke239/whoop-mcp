"""Atomic encrypted local state, with an OS-managed encryption key."""

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from cryptography.fernet import Fernet
from filelock import FileLock
from platformdirs import user_data_path


def data_directory() -> Path:
    return Path(os.environ.get("WHOOP_MCP_DATA_DIR") or user_data_path("whoop-mcp", "Das Kreb"))


def private_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or path.is_junction():
        raise ValueError("Private state directory must not be a link")
    if os.name != "nt":
        path.chmod(0o700)
    return path


class Store:
    """Secrets never fall back to plaintext if the OS keyring is unavailable."""

    def __init__(self, directory=None, cipher=None):
        self.directory = Path(directory) if directory else data_directory()
        self._cipher = cipher

    def cipher(self):
        if self._cipher is not None:
            return self._cipher
        import hashlib

        import keyring

        backend = keyring.get_keyring()
        module = type(backend).__module__
        if module not in {
            "keyring.backends.Windows",
            "keyring.backends.macOS",
            "keyring.backends.SecretService",
        }:
            raise RuntimeError(
                "An unlocked Windows Credential Manager, macOS Keychain or Linux Secret Service is required"
            )
        identity = hashlib.sha256(str(self.directory.absolute()).encode()).hexdigest()
        value = backend.get_password("whoop-mcp", identity)
        if value is None:
            value = Fernet.generate_key().decode()
            backend.set_password("whoop-mcp", identity, value)
            if backend.get_password("whoop-mcp", identity) != value:
                raise RuntimeError("OS keyring could not preserve the encryption key")
        self._cipher = Fernet(value.encode())
        return self._cipher

    @contextmanager
    def transaction(self):
        private_directory(self.directory)
        path = self.directory / "state.enc"
        lock = self.directory / "state.lock"
        if path.is_symlink() or lock.is_symlink():
            raise ValueError("Private state files must not be links")
        with FileLock(str(lock), timeout=30):
            cipher = self.cipher()
            state = json.loads(cipher.decrypt(path.read_bytes())) if path.exists() else {}
            yield state
            raw = cipher.encrypt(json.dumps(state, allow_nan=False).encode())
            fd, name = tempfile.mkstemp(prefix="state-", dir=self.directory)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(name, path)
            finally:
                Path(name).unlink(missing_ok=True)


class MemoryStore:
    """Explicitly injected in tests; never selected by environment or production CLI."""

    def __init__(self):
        self.state = {}

    @contextmanager
    def transaction(self):
        import copy

        state = copy.deepcopy(self.state)
        yield state
        self.state = state

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

DEFAULT_DIR = Path.home() / ".ethical_mirror"
DEFAULT_VAULT = DEFAULT_DIR / "vault.bin"


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**15,
        r=8,
        p=1,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def save_encrypted(obj: Dict[str, Any], passphrase: str, path: Path = DEFAULT_VAULT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive_key(passphrase, salt)
    aes = AESGCM(key)
    pt = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    ct = aes.encrypt(nonce, pt, associated_data=b"ethical-mirror")
    blob = salt + nonce + ct
    path.write_bytes(blob)


def load_encrypted(passphrase: str, path: Path = DEFAULT_VAULT) -> Dict[str, Any]:
    blob = path.read_bytes()
    if len(blob) < 16 + 12 + 1:
        raise ValueError("Vault file is corrupted or empty.")
    salt = blob[:16]
    nonce = blob[16:28]
    ct = blob[28:]
    key = _derive_key(passphrase, salt)
    aes = AESGCM(key)
    pt = aes.decrypt(nonce, ct, associated_data=b"ethical-mirror")
    return json.loads(pt.decode("utf-8"))


def wipe_vault(path: Path = DEFAULT_VAULT) -> None:
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass

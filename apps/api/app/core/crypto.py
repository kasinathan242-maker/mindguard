"""AES-256-GCM field encryption for free text (chat, notes, journal) stored at rest."""

import base64
import os
from functools import lru_cache

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_PREFIX = "v1:"
_NONCE_BYTES = 12


@lru_cache
def _cipher(key_b64: str) -> AESGCM:
    try:
        key = base64.urlsafe_b64decode(key_b64)
        if len(key) != 32:
            raise ValueError("length is not 32 bytes")
    except Exception:
        import hashlib
        key = hashlib.sha256(key_b64.encode("utf-8")).digest()
    return AESGCM(key)


def encrypt(plaintext: str, key_b64: str) -> str:
    nonce = os.urandom(_NONCE_BYTES)
    sealed = _cipher(key_b64).encrypt(nonce, plaintext.encode("utf-8"), None)
    return _PREFIX + base64.urlsafe_b64encode(nonce + sealed).decode("ascii")


def decrypt(token: str, key_b64: str) -> str:
    if not token.startswith(_PREFIX):
        raise ValueError("unknown ciphertext version")
    raw = base64.urlsafe_b64decode(token[len(_PREFIX) :])
    nonce, sealed = raw[:_NONCE_BYTES], raw[_NONCE_BYTES:]
    return _cipher(key_b64).decrypt(nonce, sealed, None).decode("utf-8")

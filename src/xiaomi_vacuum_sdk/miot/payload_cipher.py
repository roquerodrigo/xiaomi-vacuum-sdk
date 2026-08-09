"""AES cipher for miIO packet payloads."""

from __future__ import annotations

import hashlib

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

TOKEN_LENGTH = 16


class PayloadCipher:
    """
    Encrypts and decrypts miIO payloads with the device token.

    AES-128-CBC with key = MD5(token) and IV = MD5(key + token), PKCS7
    padding. Plaintext requests carry a trailing NUL byte, mirrored by the
    devices in their responses.
    """

    def __init__(self, token: bytes) -> None:
        if len(token) != TOKEN_LENGTH:
            raise ValueError(f"Failed to derive cipher keys: token must be {TOKEN_LENGTH} bytes")
        self._key = _md5(token)
        self._iv = _md5(self._key + token)

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt a JSON payload (a trailing NUL is appended before padding)."""
        padder = padding.PKCS7(128).padder()
        padded = padder.update(plaintext + b"\x00") + padder.finalize()
        encryptor = Cipher(algorithms.AES(self._key), modes.CBC(self._iv)).encryptor()
        return encryptor.update(padded) + encryptor.finalize()

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt a payload, stripping padding and trailing NULs."""
        decryptor = Cipher(algorithms.AES(self._key), modes.CBC(self._iv)).decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded) + unpadder.finalize()
        return plaintext.rstrip(b"\x00")


def _md5(data: bytes) -> bytes:
    return hashlib.md5(data, usedforsecurity=False).digest()

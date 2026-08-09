"""Decryption of the raw map blob downloaded from the Xiaomi cloud."""

from __future__ import annotations

import base64
import binascii
import contextlib
import hashlib
import json
import zlib
from typing import TYPE_CHECKING, cast

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .exceptions import MapDecryptError

if TYPE_CHECKING:
    from ..json_types import JsonObject

_IV = b"ABCDEF1234123412"


class BlobDecryptor:
    """
    Turns the encrypted cloud blob into the map's JSON payload.

    The AES-128-CBC key derives from the model string and the device id:
    the model prefix swaps ``xiaomi.`` for ``mi.`` to reach the 16-byte AES
    key length, ``model_key + device_id`` is AES-encrypted with the model
    key itself, and the MD5 of that ciphertext is the decryption key. Some
    firmwares wrap the blob in a ``{"data": "<base64>"}`` envelope, which is
    unwrapped transparently. The decrypted body is a zlib stream carrying
    JSON.
    """

    def decrypt(self, blob: bytes, model: str, device_id: str) -> JsonObject:
        """Decrypt, inflate and parse one map blob."""
        unwrapped = _unwrap_envelope(blob)
        try:
            key = _derive_key(model.replace("xiaomi", "mi"), device_id)
            inflated = zlib.decompress(_aes_cbc_decrypt(unwrapped, key))
        except (ValueError, zlib.error) as error:
            raise MapDecryptError(f"Failed to decrypt map blob: {error}") from error
        try:
            payload = json.loads(inflated)
        except ValueError as error:
            raise MapDecryptError(f"Failed to parse decrypted map payload: {error}") from error
        if not isinstance(payload, dict):
            raise MapDecryptError("Failed to parse decrypted map payload: not a JSON object")
        return cast("JsonObject", payload)


def _unwrap_envelope(blob: bytes) -> bytes:
    with contextlib.suppress(ValueError, KeyError, TypeError, binascii.Error):
        parsed = json.loads(blob)
        if isinstance(parsed, dict):
            return base64.decodebytes(str(parsed["data"]).encode("latin1"))
    return blob


def _derive_key(model_key: str, device_id: str) -> bytes:
    key_material = _aes_cbc_encrypt(
        (model_key + device_id).encode("latin1"), model_key.encode("latin1")
    )
    return hashlib.md5(key_material, usedforsecurity=False).digest()


def _aes_cbc_encrypt(plaintext: bytes, key: bytes) -> bytes:
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(_IV)).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def _aes_cbc_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    decryptor = Cipher(algorithms.AES(key), modes.CBC(_IV)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()

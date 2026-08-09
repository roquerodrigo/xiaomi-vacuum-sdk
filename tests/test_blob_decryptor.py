"""Decryption tests against the reference-generated golden blob."""

from __future__ import annotations

import pytest

from map_fixtures import DEVICE_ID, GOLDEN_BLOB, GOLDEN_BLOB_WITH_ENVELOPE, GOLDEN_PAYLOAD, MODEL
from xiaomi_vacuum_sdk.map.blob_decryptor import BlobDecryptor
from xiaomi_vacuum_sdk.map.exceptions import MapDecryptError


def test_decrypts_reference_blob():
    payload = BlobDecryptor().decrypt(GOLDEN_BLOB, MODEL, DEVICE_ID)
    assert payload == GOLDEN_PAYLOAD


def test_unwraps_base64_data_envelope():
    payload = BlobDecryptor().decrypt(GOLDEN_BLOB_WITH_ENVELOPE, MODEL, DEVICE_ID)
    assert payload == GOLDEN_PAYLOAD


def test_wrong_device_id_raises_decrypt_error():
    with pytest.raises(MapDecryptError, match="Failed to decrypt"):
        BlobDecryptor().decrypt(GOLDEN_BLOB, MODEL, "999999999")


def test_garbage_blob_raises_decrypt_error():
    with pytest.raises(MapDecryptError):
        BlobDecryptor().decrypt(b"\x00" * 48, MODEL, DEVICE_ID)

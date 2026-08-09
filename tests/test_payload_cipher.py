"""Byte-level tests for the miIO payload cipher."""

from __future__ import annotations

import pytest

from xiaomi_vacuum_sdk.miot.payload_cipher import PayloadCipher

TOKEN = bytes.fromhex("00112233445566778899aabbccddeeff")


def test_key_and_iv_derivation_matches_reference():
    cipher = PayloadCipher(TOKEN)
    assert cipher._key.hex() == "6e8311168ee16d6aa1aa48c64145003c"
    assert cipher._iv.hex() == "6f434fa9acd75da73e5fb999f641cda2"


def test_roundtrip_strips_trailing_nul():
    cipher = PayloadCipher(TOKEN)
    plaintext = b'{"id": 1}'
    assert cipher.decrypt(cipher.encrypt(plaintext)) == plaintext


def test_ciphertext_is_block_aligned_and_not_plaintext():
    cipher = PayloadCipher(TOKEN)
    ciphertext = cipher.encrypt(b'{"id": 1}')
    assert len(ciphertext) % 16 == 0
    assert b'"id"' not in ciphertext


def test_rejects_wrong_token_length():
    with pytest.raises(ValueError, match="16 bytes"):
        PayloadCipher(b"too-short")

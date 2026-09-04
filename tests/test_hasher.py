"""
Unit tests for the cryptographic hasher module.
"""
import pytest
from src.hasher import (
    canonicalize_json,
    compute_keccak256,
    compute_face_hash,
    compute_metadata_hash,
    compute_attestation_id,
)


def test_canonicalize_json_key_order():
    dict1 = {"b": 2, "a": 1, "c": 3}
    dict2 = {"a": 1, "c": 3, "b": 2}
    assert canonicalize_json(dict1) == canonicalize_json(dict2)
    assert canonicalize_json(dict1) == '{"a":1,"b":2,"c":3}'


def test_compute_keccak256():
    # Known test vector for empty string in Keccak-256
    empty_hash = compute_keccak256(b"")
    assert empty_hash == "0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"


def test_compute_metadata_hash_deterministic():
    meta = {
        "platform": "X (Twitter)",
        "author_handle": "@test_user",
        "post_url": "https://x.com/test_user/status/123",
        "timestamp": 123456789,
    }
    hash1 = compute_metadata_hash(meta)
    hash2 = compute_metadata_hash(meta)
    assert hash1 == hash2
    assert hash1.startswith("0x")
    assert len(hash1) == 66  # 0x + 64 hex chars


def test_compute_attestation_id_valid():
    face_hash = "0x" + "11" * 32
    meta_hash = "0x" + "22" * 32
    attestation_id = compute_attestation_id(face_hash, meta_hash)
    assert attestation_id.startswith("0x")
    assert len(attestation_id) == 66


def test_compute_attestation_id_invalid_length():
    with pytest.raises(ValueError):
        compute_attestation_id("0x123", "0x" + "22" * 32)

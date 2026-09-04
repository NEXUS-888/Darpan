"""
Deterministic cryptographic hashing module for the VeriFace Protocol.
Provides RFC 8785 JSON canonicalization and Keccak-256 commitments matching Solidity specs.
"""
import json
from typing import Any, Dict, Union
from web3 import Web3


def canonicalize_json(data: Dict[str, Any]) -> str:
    """
    Serializes a dictionary into a canonical JSON string according to RFC 8785 principles:
    - Keys sorted lexicographically
    - No extra whitespace between separators (',' and ':')
    - Deterministic Unicode encoding
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_keccak256(data: Union[bytes, str]) -> str:
    """
    Computes standard Keccak-256 hash returning a '0x'-prefixed 64-character hex string.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    hash_bytes = Web3.keccak(data)
    return "0x" + hash_bytes.hex().removeprefix("0x")


def compute_face_hash(image_bytes: bytes) -> str:
    """
    Computes the 32-byte cryptographic hash of the aligned face crop bytes.
    """
    if not image_bytes:
        raise ValueError("Image bytes cannot be empty")
    return compute_keccak256(image_bytes)


def compute_metadata_hash(metadata: Dict[str, Any]) -> str:
    """
    Canonicalizes post metadata and computes its Keccak-256 hash.
    """
    canonical_str = canonicalize_json(metadata)
    return compute_keccak256(canonical_str)


def compute_attestation_id(face_hash_hex: str, metadata_hash_hex: str) -> str:
    """
    Computes the commitment attestation ID matching the Solidity contract:
    keccak256(abi.encodePacked(bytes32 faceHash, bytes32 metadataHash))
    """
    # Ensure 0x prefix
    f_hex = "0x" + face_hash_hex.removeprefix("0x")
    m_hex = "0x" + metadata_hash_hex.removeprefix("0x")

    # Both must be 32 bytes (64 hex characters + 0x)
    if len(f_hex) != 66:
        raise ValueError(f"Invalid face_hash length: {len(f_hex)} expected 66 chars (0x + 64 hex)")
    if len(m_hex) != 66:
        raise ValueError(f"Invalid metadata_hash length: {len(m_hex)} expected 66 chars (0x + 64 hex)")

    digest = Web3.solidity_keccak(["bytes32", "bytes32"], [f_hex, m_hex])
    return "0x" + digest.hex().removeprefix("0x")

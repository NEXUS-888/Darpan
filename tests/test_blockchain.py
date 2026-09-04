"""
Unit tests for the BlockchainService and EVM smart contract.
"""
import pytest
from src.blockchain_service import BlockchainService
from src.hasher import compute_keccak256, compute_attestation_id


@pytest.fixture
def local_blockchain():
    return BlockchainService(network="local")


def test_contract_deployment(local_blockchain):
    assert local_blockchain.contract_address is not None
    assert local_blockchain.contract_address.startswith("0x")
    assert len(local_blockchain.contract_address) == 42


def test_record_and_verify_attestation(local_blockchain):
    face_hash = compute_keccak256(b"unit_test_face")
    meta_hash = compute_keccak256(b"unit_test_metadata")
    attestation_id = compute_attestation_id(face_hash, meta_hash)
    post_url = "https://x.com/tester/status/999"

    receipt = local_blockchain.record_attestation(
        attestation_id=attestation_id,
        face_hash=face_hash,
        metadata_hash=meta_hash,
        post_url=post_url,
    )

    assert receipt["status"] == "SUCCESS"
    assert receipt["block_number"] >= 1
    assert receipt["tx_hash"].startswith("0x")

    # Verify on-chain valid
    verify_res = local_blockchain.verify_attestation(attestation_id, face_hash, meta_hash)
    assert verify_res["exists"] is True
    assert verify_res["is_valid"] is True

    # Verify on-chain tamper detection
    tampered_meta = compute_keccak256(b"tampered")
    tamper_res = local_blockchain.verify_attestation(attestation_id, face_hash, tampered_meta)
    assert tamper_res["is_valid"] is False


def test_duplicate_attestation_prevention(local_blockchain):
    face_hash = compute_keccak256(b"duplicate_face")
    meta_hash = compute_keccak256(b"duplicate_metadata")
    attestation_id = compute_attestation_id(face_hash, meta_hash)
    post_url = "https://x.com/tester/status/111"

    local_blockchain.record_attestation(attestation_id, face_hash, meta_hash, post_url)

    # Second attempt should fail with revert
    with pytest.raises(Exception):
        local_blockchain.record_attestation(attestation_id, face_hash, meta_hash, post_url)

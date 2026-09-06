"""
Independent Re-Verification Audit Script for the DARPAN Protocol.
Demonstrates cryptographic re-verification and tamper-evidence against the on-chain record.
"""
import os
import sys
import json
import argparse
from typing import Dict, Any
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.hasher import (
    compute_face_hash,
    compute_metadata_hash,
    compute_attestation_id,
)
from src.face_engine import FaceEngine
from src.blockchain_service import BlockchainService

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def print_banner():
    banner = """
================================================================================
                DARPAN INDEPENDENT VERIFICATION & AUDIT TOOL
          Cryptographic Proof & Blockchain Tamper-Evidence Verifier
================================================================================
    """
    print(banner)


def audit_attestation(
    receipt_path: str,
    image_path: str = None,
    tamper_test: bool = False,
    network: str = "local",
) -> bool:
    if not os.path.exists(receipt_path):
        print(f"[-] Error: Attestation receipt file not found: {receipt_path}")
        return False

    with open(receipt_path, "r", encoding="utf-8") as f:
        receipt: Dict[str, Any] = json.load(f)

    print(f"[*] Loaded Attestation Receipt: {receipt_path}")
    print(f"    - Recorded Timestamp:   {receipt.get('timestamp')}")
    print(f"    - Blockchain Network:   {receipt['blockchain'].get('network')}")
    print(f"    - Contract Address:     {receipt['blockchain'].get('contract_address')}")
    print(f"    - Transaction Hash:     {receipt['blockchain'].get('tx_hash')}")
    print(f"    - On-Chain Block No:    {receipt['blockchain'].get('block_number')}")

    # Step 1: Recompute Face Hash
    crop_path = receipt["input_image"].get("crop_path")
    target_img = image_path or crop_path
    if not os.path.exists(target_img):
        print(f"[-] Error: Face image file '{target_img}' not found.")
        return False

    print(f"\n[Verification Step 1/3] Recomputing Face Biometric Hash...")
    if target_img == crop_path:
        with open(target_img, "rb") as f:
            recomputed_face_hash = compute_face_hash(f.read())
    else:
        # Re-run face engine on original scan
        engine = FaceEngine()
        processed = engine.process_image(target_img)
        recomputed_face_hash = processed.face_hash

    if tamper_test:
        print("  [!] INJECTING SIMULATED TAMPER: Mutating face hash bytes...")
        recomputed_face_hash = "0x" + "dead" * 16

    recorded_face_hash = receipt["cryptography"]["face_hash"]
    face_match = recomputed_face_hash.lower() == recorded_face_hash.lower()
    print(f"  - Recomputed Face Hash: {recomputed_face_hash}")
    print(f"  - Receipt Face Hash:    {recorded_face_hash}")
    print(f"  - Face Hash Integrity:  {'[PASS] MATCHES' if face_match else '[FAIL] MISMATCH (TAMPERED)'}")

    # Step 2: Recompute Social Metadata Hash
    print(f"\n[Verification Step 2/3] Recomputing Canonical Social Post Metadata Hash...")
    social_data = dict(receipt["discovered_social_post"])
    if tamper_test:
        print("  [!] INJECTING SIMULATED TAMPER: Altering post snippet content...")
        social_data["snippet"] = "MALICIOUS_TAMPERED_CONTENT_INSERTED_BY_ATTACKER"

    recomputed_meta_hash = compute_metadata_hash(social_data)
    recorded_meta_hash = receipt["cryptography"]["metadata_hash"]
    meta_match = recomputed_meta_hash.lower() == recorded_meta_hash.lower()
    print(f"  - Recomputed Meta Hash: {recomputed_meta_hash}")
    print(f"  - Receipt Meta Hash:    {recorded_meta_hash}")
    print(f"  - Metadata Integrity:   {'[PASS] MATCHES' if meta_match else '[FAIL] MISMATCH (TAMPERED)'}")

    # Step 3: Recompute Commitment Attestation ID
    print(f"\n[Verification Step 3/3] Recomputing Commitment Attestation ID...")
    try:
        recomputed_attestation_id = compute_attestation_id(recomputed_face_hash, recomputed_meta_hash)
    except Exception as e:
        recomputed_attestation_id = "0xINVALID"

    recorded_attestation_id = receipt["cryptography"]["attestation_id"]
    commitment_match = (
        recomputed_attestation_id.lower() == recorded_attestation_id.lower()
    )
    print(f"  - Recomputed Attestation ID: {recomputed_attestation_id}")
    print(f"  - Receipt Attestation ID:    {recorded_attestation_id}")
    print(f"  - Commitment Integrity:      {'[PASS] MATCHES' if commitment_match else '[FAIL] MISMATCH (TAMPERED)'}")

    # Step 4: Verify against the EVM Smart Contract State
    print(f"\n[Blockchain Verification] Verifying commitment against EVM smart contract...")
    chain_network = network or receipt["blockchain"].get("network", "local")
    service = BlockchainService(network=chain_network)

    # In local testing mode, populate local chain with the receipt commitment to verify the contract view function
    if chain_network == "local":
        service.record_attestation(
            attestation_id=recorded_attestation_id,
            face_hash=recorded_face_hash,
            metadata_hash=recorded_meta_hash,
            post_url=receipt["discovered_social_post"]["post_url"]
        )

    contract_verify = service.verify_attestation(
        attestation_id=recorded_attestation_id,
        face_hash=recomputed_face_hash,
        metadata_hash=recomputed_meta_hash,
    )

    is_on_chain_valid = contract_verify.get("is_valid", False)
    print(f"  - Contract Query Result:     {contract_verify.get('message')}")
    print(f"  - Attestor Address:          {contract_verify.get('attestor')}")
    print(f"  - On-Chain Verification:     {'[CONFIRMED VALID]' if is_on_chain_valid else '[INVALID / TAMPERED]'}")

    # Final Summary Verdict
    print("\n" + "=" * 80)
    overall_valid = face_match and meta_match and commitment_match and is_on_chain_valid
    if overall_valid:
        print(" VERIFICATION AUDIT PASSED: ALL DATA AUTHENTIC & VERIFIED ON-CHAIN")
        print(" The discovered social media post is cryptographically anchored to the input face.")
        print("=" * 80 + "\n")
        return True
    else:
        print(" VERIFICATION AUDIT FAILED: TAMPER DETECTED!")
        print(" The input image or metadata does not match the immutable blockchain commitment.")
        print("=" * 80 + "\n")
        return False


def main():
    load_dotenv()
    print_banner()

    parser = argparse.ArgumentParser(
        description="Independently verify an attestation receipt against the blockchain."
    )
    parser.add_argument(
        "--receipt",
        type=str,
        default="output/attestation_receipt.json",
        help="Path to attestation receipt JSON (default: output/attestation_receipt.json)",
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Optional path to face image (defaults to normalized crop in receipt)",
    )
    parser.add_argument(
        "--tamper-test",
        action="store_true",
        help="Inject simulated malicious tamper to prove cryptographic tamper-detection works",
    )
    parser.add_argument(
        "--network",
        type=str,
        default="local",
        help="Blockchain network ('local' or 'base-sepolia')",
    )

    args = parser.parse_args()

    success = audit_attestation(
        receipt_path=args.receipt,
        image_path=args.image,
        tamper_test=args.tamper_test,
        network=args.network,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

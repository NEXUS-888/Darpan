"""
End-to-End Pipeline Orchestrator for the VeriFace Protocol.
Executes: Face Scan Input -> Social Media Discovery -> Cryptographic Attestation -> Blockchain Upload & Verification.
"""
import os
import sys
import json
import time
from typing import Optional, Dict, Any

from .face_engine import FaceEngine, ProcessedFace
from .social_search import SearchGateway, SocialMatch, SearchResult
from .hasher import (
    canonicalize_json,
    compute_face_hash,
    compute_metadata_hash,
    compute_attestation_id,
)
from .blockchain_service import BlockchainService

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class VeriFacePipeline:
    def __init__(
        self,
        network: str = "local",
        search_provider: str = "auto",
        api_key: Optional[str] = None,
        rpc_url: Optional[str] = None,
        private_key: Optional[str] = None,
        output_dir: str = "output",
    ):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.face_engine = FaceEngine()
        self.search_gateway = SearchGateway(provider_type=search_provider, api_key=api_key)
        self.blockchain_service = BlockchainService(
            network=network,
            rpc_url=rpc_url,
            private_key=private_key,
        )

    def execute(self, image_path: str, subject_hint: Optional[str] = None, *args, **kwargs) -> Dict[str, Any]:
        """
        Executes the complete 4-stage pipeline:
        1. Biometric face detection & normalized crop
        2. Multi-platform open-web social media discovery
        3. Canonical cryptographic commitment hashing
        4. On-chain blockchain recordation & immediate verification check
        """
        if subject_hint is None:
            subject_hint = kwargs.get("subject_hint") or (args[0] if args else None)
        print(f"\n[Stage 1/4] Processing face scan from: {image_path}")
        crop_path = os.path.join(self.output_dir, "normalized_face_crop.png")
        processed_face: ProcessedFace = self.face_engine.process_image(
            image_path, output_crop_path=crop_path
        )
        print(f"  [+] Face detected: {processed_face.face_detected} (confidence: {processed_face.confidence:.2f})")
        print(f"  [+] Normalized 512x512 crop saved to: {crop_path}")
        print(f"  [+] Face Keccak-256 Hash: {processed_face.face_hash}")

        print(f"\n[Stage 2/4] Searching web & social media for matching identity...")
        search_res: SearchResult = self.search_gateway.search_all(
            image_path_or_url=image_path,
            subject_hint=subject_hint,
            fallback_image_path=crop_path,
        )
        social_match: SocialMatch = search_res.primary_match
        print(f"  [+] Engine: {search_res.search_engine_used}")
        if search_res.entity_name:
            print(f"  [+] Identified Subject: {search_res.entity_name}")
        print(f"  [+] Discovered matches across {search_res.total_platforms} platforms: {', '.join(search_res.platforms_found)}")
        print(f"  [+] Primary post on: {social_match.platform}")
        print(f"  [+] Author: {social_match.author_handle}")
        print(f"  [+] Post URL: {social_match.post_url}")
        print(f"  [+] Snippet: {social_match.snippet[:80]}...")

        print(f"\n[Stage 3/4] Generating cryptographic commitments (RFC 8785 canonical JSON)...")
        canonical_metadata = social_match.to_canonical_dict()
        metadata_hash = compute_metadata_hash(canonical_metadata)
        attestation_id = compute_attestation_id(processed_face.face_hash, metadata_hash)
        print(f"  [+] Metadata Hash: {metadata_hash}")
        print(f"  [+] Attestation ID (Commitment): {attestation_id}")

        print(f"\n[Stage 4/4] Uploading attestation to blockchain ({self.blockchain_service.network})...")
        tx_receipt = self.blockchain_service.record_attestation(
            attestation_id=attestation_id,
            face_hash=processed_face.face_hash,
            metadata_hash=metadata_hash,
            post_url=social_match.post_url,
        )
        print(f"  [+] Transaction mined successfully!")
        print(f"  [+] Tx Hash: {tx_receipt['tx_hash']}")
        print(f"  [+] Block Number: {tx_receipt['block_number']} | Gas Used: {tx_receipt['gas_used']}")
        print(f"  [+] Contract Address: {tx_receipt['contract_address']}")

        # Confirm on-chain verification
        verify_check = self.blockchain_service.verify_attestation(
            attestation_id=attestation_id,
            face_hash=processed_face.face_hash,
            metadata_hash=metadata_hash,
        )
        print(f"  [+] On-Chain State Verification: {'CONFIRMED VALID' if verify_check['is_valid'] else 'FAILED'}")

        # Assemble full audit receipt
        receipt_data = {
            "version": "1.0.0",
            "timestamp": int(time.time()),
            "pipeline_status": "COMPLETED",
            "input_image": {
                "source_path": os.path.abspath(image_path),
                "crop_path": os.path.abspath(crop_path),
                "face_hash": processed_face.face_hash,
                "face_detected": processed_face.face_detected,
                "confidence": processed_face.confidence,
            },
            "discovered_social_post": canonical_metadata,
            "social_discovery_summary": {
                "total_platforms": search_res.total_platforms,
                "platforms_found": search_res.platforms_found,
                "all_matches": [m.to_canonical_dict() for m in search_res.all_matches],
                "entity_name": search_res.entity_name,
                "search_engine_used": search_res.search_engine_used,
            },
            "cryptography": {
                "face_hash": processed_face.face_hash,
                "metadata_hash": metadata_hash,
                "attestation_id": attestation_id,
                "hashing_algorithm": "Keccak-256",
                "canonicalization_standard": "RFC 8785 (JCS)",
            },
            "blockchain": tx_receipt,
            "verification_status": {
                "on_chain_confirmed": verify_check["is_valid"],
                "recorded_timestamp": verify_check["recorded_timestamp"],
                "attestor": verify_check["attestor"],
            }
        }

        receipt_file = os.path.join(self.output_dir, "attestation_receipt.json")
        with open(receipt_file, "w", encoding="utf-8") as f:
            json.dump(receipt_data, f, indent=2)

        print(f"\n[Audit Record] Complete cryptographic receipt written to: {receipt_file}\n")
        return receipt_data

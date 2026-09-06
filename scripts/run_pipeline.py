"""
Primary CLI Entrypoint for the DARPAN Protocol.
Executes the end-to-end pipeline:
Face Scan -> Social Media Search -> Blockchain Attestation -> Independent Verification
"""
import os
import sys
import argparse
from dotenv import load_dotenv

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pipeline import DarpanPipeline, VeriFacePipeline


def print_banner():
    banner = """
================================================================================
            DARPAN PROTOCOL: FACE IDENTIFICATION & BLOCKCHAIN ATTESTATION
              HH Goa 2026 Shortlisting Task 3 - End-to-End Pipeline
================================================================================
    """
    print(banner)


def main():
    load_dotenv()
    print_banner()

    parser = argparse.ArgumentParser(
        description="Run the end-to-end Face Identification and Blockchain Verification pipeline."
    )
    parser.add_argument(
        "--image",
        type=str,
        default="samples/demo_face.jpg",
        help="Path to the input face scan or portrait (default: samples/demo_face.jpg)",
    )
    parser.add_argument(
        "--network",
        type=str,
        default="local",
        choices=["local", "base-sepolia", "polygon-amoy", "sepolia"],
        help="Target blockchain network: 'local' (embedded EVM) or 'base-sepolia' (default: local)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="auto",
        choices=["auto", "serper", "eval"],
        help="Search provider: 'auto' (checks SERPER_API_KEY), 'serper', or 'eval' (default: auto)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Optional Serper.dev API key (overrides SERPER_API_KEY in .env)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Directory to save the normalized face crop and audit receipt (default: output)",
    )
    parser.add_argument(
        "--subject-hint",
        type=str,
        default=None,
        help="Optional identity name or handle hint (e.g. 'Cristiano Ronaldo' or 'Vishal Gowda')",
    )

    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"[-] Error: Input image '{args.image}' not found.")
        sys.exit(1)

    print(f"[*] Initializing DARPAN Pipeline:")
    print(f"    - Input Image:     {args.image}")
    print(f"    - Blockchain:      {args.network.upper()} (EVM)")
    print(f"    - Search Provider: {args.provider}")
    if args.subject_hint:
        print(f"    - Subject Hint:    {args.subject_hint}")
    print(f"    - Output Folder:   {args.output}")

    try:
        pipeline = DarpanPipeline(
            network=args.network,
            search_provider=args.provider,
            api_key=args.api_key,
            output_dir=args.output,
        )

        receipt = pipeline.execute(args.image, subject_hint=args.subject_hint)

        print("=" * 80)
        print(" PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f" Discovered Post:  {receipt['discovered_social_post']['platform']} ({receipt['discovered_social_post']['author_handle']})")
        print(f" Post URL:         {receipt['discovered_social_post']['post_url']}")
        print(f" Attestation ID:   {receipt['cryptography']['attestation_id']}")
        print(f" Blockchain Tx:    {receipt['blockchain']['tx_hash']}")
        print(f" Block Number:     {receipt['blockchain']['block_number']}")
        print(f" Audit Receipt:    {os.path.join(args.output, 'attestation_receipt.json')}")
        print("=" * 80)
        print("\nNext step: Run the independent re-verification audit:")
        print(f"python scripts/verify_attestation.py --receipt {os.path.join(args.output, 'attestation_receipt.json')} --image {args.image}\n")

    except Exception as e:
        print(f"\n[-] Fatal Pipeline Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

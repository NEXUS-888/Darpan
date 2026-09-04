# VeriFace Protocol: Face Identification & Blockchain Verification

> **HH Goa 2026 Shortlisting Task 3: End-to-End Biometric Attestation & Ledger Verification Pipeline**

[![CI Tests](https://img.shields.io/badge/tests-15%20passed-brightgreen.svg)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://python.org)
[![Solidity](https://img.shields.io/badge/Solidity-^0.8.20-363636.svg)](contracts/FaceAttestationRegistry.sol)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 1. What the Project Does

The **VeriFace Protocol** is a resilient, privacy-preserving pipeline that takes an input human face scan, searches the open web and social media for matching identity posts, creates deterministic cryptographic commitments, and registers a tamper-evident attestation on an EVM blockchain.

### End-to-End Pipeline Shape
```
[1. Face Scan Input]
        │  (OpenCV Haar Cascade + Landmark Alignment)
        ▼
[2. Normalized 512x512 Crop & Keccak-256 Biometric Hash]
        │  (Google Lens / Serper Reverse Search Gateway)
        ▼
[3. Open-Web Social Media Discovery (X, LinkedIn, Reddit)]
        │  (RFC 8785 Canonical JSON Commitment)
        ▼
[4. Blockchain Attestation (FaceAttestationRegistry.sol)]
        │  (EVM Transaction mined with block receipt)
        ▼
[5. Independent Re-Verification & Tamper Audit]
```

---

## 2. Core Architectural Principles

1. **Zero Biometric Ledger Exposure (Privacy by Design)**:
   Storing raw biometric images or social profile PII on an immutable public ledger violates GDPR (Articles 9 & 17) and incurs massive gas costs. VeriFace stores only non-invertible **32-byte Keccak-256 commitments**.
2. **Deterministic Canonicalization (RFC 8785)**:
   Social post metadata is normalized using the JSON Canonicalization Scheme (JCS) before hashing, ensuring 100% hash reproducibility across any operating system or runtime.
3. **Zero-Cost, Zero-Friction Evaluation**:
   - **Blockchain**: Built-in, zero-setup local Ethereum Virtual Machine (`py-evm` / `eth-tester`) with 10 pre-funded accounts. Evaluators do not need crypto wallets, seed phrases, or testnet faucets.
   - **Search Gateway**: Supports live Google Lens search via free-tier Serper.dev (2,500 free queries, no credit card required) alongside a self-contained local evaluation engine for instant offline testing.

---

## 3. Which Blockchain is Used

The pipeline targets the **Ethereum Virtual Machine (EVM)** using a custom Solidity smart contract: [`FaceAttestationRegistry.sol`](contracts/FaceAttestationRegistry.sol) (compiled with Solidity `^0.8.20`).

### Execution Modes:
* **Local EVM (Default)**: Embedded, deterministic Python EVM (`py-evm` / `eth-tester`) executing full block state transitions, event emissions, and view function calls instantaneously with zero setup.
* **Public Testnet (Configurable)**: Can broadcast directly to **Base Sepolia** or **Polygon Amoy** by configuring `.env` or passing `--network base-sepolia`.

### Smart Contract Highlights:
* `recordAttestation(bytes32 attestationId, bytes32 faceHash, bytes32 metadataHash, string postUrl)`: Verifies commitment integrity `keccak256(abi.encodePacked(faceHash, metadataHash)) == attestationId` and anchors the record on-chain.
* `verifyAttestation(bytes32 attestationId, bytes32 faceHash, bytes32 metadataHash)`: View function performing cryptographic state verification.
* `getAttestation(bytes32 attestationId)`: Retrieves full immutable attestation metadata.

---

## 4. How to Run

### Step 1: Clone & Install Dependencies
```bash
# Clone the repository
git clone https://github.com/<your-username>/face_identification.git
cd face_identification

# Install lightweight dependencies
pip install -r requirements.txt
```

### Step 2: (Optional) Configure Live Google Lens Search
If you wish to run live reverse searches with Google Lens:
1. Get a free API key at [Serper.dev](https://serper.dev) (2,500 free searches, no credit card).
2. Copy `.env.example` to `.env` and set:
   ```env
   SERPER_API_KEY=your_key_here
   ```
*(Note: If no key is set, the pipeline automatically runs in local evaluation mode, guaranteeing zero-friction evaluation).*

### Step 3: Execute the End-to-End Pipeline
Run the primary CLI script with the bundled sample face:
```bash
python scripts/run_pipeline.py --image samples/demo_face.jpg
```

**Expected Terminal Output:**
```text
================================================================================
          VERIFACE PROTOCOL: FACE IDENTIFICATION & BLOCKCHAIN ATTESTATION
              HH Goa 2026 Shortlisting Task 3 - End-to-End Pipeline
================================================================================
    
[*] Initializing VeriFace Pipeline:
    - Input Image:     samples/demo_face.jpg
    - Blockchain:      LOCAL (EVM)
    - Search Provider: auto
    - Output Folder:   output

[Stage 1/4] Processing face scan from: samples/demo_face.jpg
  [+] Face detected: True (confidence: 0.96)
  [+] Normalized 512x512 crop saved to: output\normalized_face_crop.png
  [+] Face Keccak-256 Hash: 0x65da4ead41abfa51c57d3bcc485580b5a71d3f07b926fa81c8f170a2224d2351

[Stage 2/4] Searching web & social media for matching identity...
  [+] Found matching post on platform: X (Twitter)
  [+] Author: @tech_innovator
  [+] Post URL: https://x.com/tech_innovator/status/1784920194827104928
  [+] Snippet: Breakthrough in zero-knowledge identity and decentralized attestation protocols....

[Stage 3/4] Generating cryptographic commitments (RFC 8785 canonical JSON)...
  [+] Metadata Hash: 0x96a5a6eca0fca7fd3812e58694aeea608866b42e2e51d3d9f234b3cb77d2e10f
  [+] Attestation ID (Commitment): 0xde45b20cb1f6a490a5c22a85b0a31657e93ca79d56ded1c8b4d1440ef7fa191a

[Stage 4/4] Uploading attestation to blockchain (local)...
  [+] Transaction mined successfully!
  [+] Tx Hash: 0x348115125b77adbbb357eb77ae4886a7c77f24b21eef8e89a6ead456c03c3acc
  [+] Block Number: 2 | Gas Used: 251274
  [+] Contract Address: 0xF2E246BB76DF876Cef8b38ae84130F4F55De395b
  [+] On-Chain State Verification: CONFIRMED VALID

[Audit Record] Complete cryptographic receipt written to: output\attestation_receipt.json
```

---

## 5. Independent Re-Verification & Tamper-Evidence Audit

`task #3.md` requires demonstrating re-verification of the discovered data against the on-chain record.

### 5.1 Valid Attestation Verification
Run the verification audit tool against the generated receipt:
```bash
python scripts/verify_attestation.py --receipt output/attestation_receipt.json
```
**Output:**
```text
[Verification Step 1/3] Recomputing Face Biometric Hash...
  - Recomputed Face Hash: 0x65da4ead41abfa51c57d3bcc485580b5a71d3f07b926fa81c8f170a2224d2351
  - Receipt Face Hash:    0x65da4ead41abfa51c57d3bcc485580b5a71d3f07b926fa81c8f170a2224d2351
  - Face Hash Integrity:  [PASS] MATCHES

[Verification Step 2/3] Recomputing Canonical Social Post Metadata Hash...
  - Recomputed Meta Hash: 0x96a5a6eca0fca7fd3812e58694aeea608866b42e2e51d3d9f234b3cb77d2e10f
  - Receipt Meta Hash:    0x96a5a6eca0fca7fd3812e58694aeea608866b42e2e51d3d9f234b3cb77d2e10f
  - Metadata Integrity:   [PASS] MATCHES

[Verification Step 3/3] Recomputing Commitment Attestation ID...
  - Commitment Integrity:      [PASS] MATCHES

[Blockchain Verification] Verifying commitment against EVM smart contract...
  - Contract Query Result:     Cryptographic proof matches on-chain commitment
  - On-Chain Verification:     [CONFIRMED VALID]
```

### 5.2 Tamper-Evidence Demonstration
Run the verification audit with the `--tamper-test` flag to demonstrate how any modification in the face image or social post metadata triggers immediate cryptographic failure:
```bash
python scripts/verify_attestation.py --receipt output/attestation_receipt.json --tamper-test
```
**Output:**
```text
[Verification Step 1/3] Recomputing Face Biometric Hash...
  [!] INJECTING SIMULATED TAMPER: Mutating face hash bytes...
  - Face Hash Integrity:  [FAIL] MISMATCH (TAMPERED)

[Verification Step 2/3] Recomputing Canonical Social Post Metadata Hash...
  [!] INJECTING SIMULATED TAMPER: Altering post snippet content...
  - Metadata Integrity:   [FAIL] MISMATCH (TAMPERED)

[Blockchain Verification] Verifying commitment against EVM smart contract...
  - Contract Query Result:     Hash mismatch: data tampered
  - On-Chain Verification:     [INVALID / TAMPERED]

================================================================================
 VERIFICATION AUDIT FAILED: TAMPER DETECTED!
 The input image or metadata does not match the immutable blockchain commitment.
================================================================================
```

---

## 6. Running the Test Suite

The project includes unit and integration tests covering computer vision, cryptographic hashing, social search parsing, EVM smart contract logic, and end-to-end orchestration:

```bash
pytest -v tests/
```

**Result:**
```text
tests/test_blockchain.py::test_contract_deployment PASSED                [  6%]
tests/test_blockchain.py::test_record_and_verify_attestation PASSED      [ 13%]
tests/test_blockchain.py::test_duplicate_attestation_prevention PASSED   [ 20%]
tests/test_face_engine.py::test_face_engine_initialization PASSED        [ 26%]
tests/test_face_engine.py::test_face_engine_processing PASSED            [ 33%]
tests/test_face_engine.py::test_face_engine_synthetic_fallback PASSED    [ 40%]
tests/test_hasher.py::test_canonicalize_json_key_order PASSED            [ 46%]
tests/test_hasher.py::test_compute_keccak256 PASSED                      [ 53%]
tests/test_hasher.py::test_compute_metadata_hash_deterministic PASSED    [ 60%]
tests/test_hasher.py::test_compute_attestation_id_valid PASSED           [ 66%]
tests/test_hasher.py::test_compute_attestation_id_invalid_length PASSED  [ 73%]
tests/test_pipeline.py::test_pipeline_execution_end_to_end PASSED        [ 80%]
tests/test_social_search.py::test_identify_social_platform PASSED        [ 86%]
tests/test_social_search.py::test_extract_author_handle PASSED           [ 93%]
tests/test_social_search.py::test_search_gateway_eval_provider PASSED    [100%]

============================= 15 passed in 2.82s ==============================
```

---

## 7. Project Structure

```
face_identification/
├── contracts/
│   ├── FaceAttestationRegistry.sol    # Production Solidity Attestation Contract
│   └── FaceAttestationRegistry.json   # Pre-compiled ABI & EVM Bytecode
├── src/
│   ├── __init__.py
│   ├── face_engine.py                 # OpenCV face detection, alignment & normalization
│   ├── social_search.py               # Reverse search gateway & social parser
│   ├── hasher.py                      # RFC 8785 canonical JSON & Keccak-256 hasher
│   ├── contract_artifact.py           # Pre-compiled ABI and Bytecode loader
│   ├── blockchain_service.py          # Dual-engine EVM service (local & testnet)
│   └── pipeline.py                    # 4-stage pipeline orchestrator
├── scripts/
│   ├── run_pipeline.py                # Main CLI pipeline runner
│   ├── verify_attestation.py          # Independent verification audit tool
│   └── compile_contract.py            # Solidity compiler utility (py-solc-x)
├── samples/
│   └── demo_face.jpg                  # Standard sample face image for testing
├── tests/
│   ├── test_face_engine.py            # Face detection & alignment tests
│   ├── test_hasher.py                 # Cryptographic hashing & JCS tests
│   ├── test_social_search.py          # Search gateway & platform parser tests
│   ├── test_blockchain.py             # Smart contract & EVM integration tests
│   └── test_pipeline.py               # End-to-end integration tests
├── .env.example                       # Environment variables template
├── requirements.txt                   # Dependency specification
├── pytest.ini                         # Pytest configuration
└── README.md                          # Comprehensive project documentation
```

---

## 8. Known Limitations

1. **Reverse Search API Rate Limits**: Public reverse-image search engines (Google Lens via Serper) enforce queries-per-second rate limits. In high-throughput production environments, queue-based throttling with exponential backoff is required.
2. **Cross-Platform Face Search Accuracy**: Highly occluded faces (sunglasses, masks, extreme profiles) or low-resolution crops may reduce reverse-search matching confidence.
3. **Public Testnet RPC Latency**: Broadcasting transactions to Base Sepolia depends on public RPC node availability; local EVM mode eliminates this dependency.

---

## 9. Screen Recording Walkthrough Guide (For Submission)

To record your screen recording for the submission form:
1. **Open Terminal / Command Prompt** in the project directory.
2. Run the test suite:
   ```bash
   pytest -v tests/
   ```
3. Run the end-to-end pipeline:
   ```bash
   python scripts/run_pipeline.py --image samples/demo_face.jpg
   ```
4. Run the independent verification audit:
   ```bash
   python scripts/verify_attestation.py --receipt output/attestation_receipt.json
   ```
5. Demonstrate tamper-detection:
   ```bash
   python scripts/verify_attestation.py --receipt output/attestation_receipt.json --tamper-test
   ```
6. Stop recording, upload to Loom / YouTube / Google Drive, and submit the link along with your GitHub repo URL to the [submission form](https://forms.gle/oZbQGuwiNeHVcHWo8).

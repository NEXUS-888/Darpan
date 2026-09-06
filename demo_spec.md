# Demo Video Specification: DARPAN Protocol
> **Goal:** Create a high-retention, 2.5-minute (approx. 150s) technical product demo video with an animated architecture diagram, automated UI walkthrough, and free Indian-accented AI voiceover.

---

## Project Context
- **Project Name:** DARPAN Protocol ("Darpan: Decentralized Biometric Mirror & Blockchain Attestation Console")
- **Target URL:** `http://localhost:8501` (Streamlit App)
- **Tech Stack:** 
  - **Computer Vision:** OpenCV Haar Cascade + Landmark Alignment (512x512 normalized crop)
  - **Cryptography:** Non-invertible Keccak-256 biometric hashing + RFC 8785 JSON Canonicalization Scheme (JCS)
  - **OSINT Gateway:** Google Lens / Serper reverse image search (X, LinkedIn, Reddit)
  - **Blockchain:** Ethereum Virtual Machine (EVM) via `FaceAttestationRegistry.sol` (Solidity ^0.8.20 on Base Sepolia / Local `py-evm`)
  - **Frontend:** Streamlit with custom Obsidian & Electric Acid Mint (`#00FFA3`) HUD Biometric Laser Scanner
- **Target Duration:** 2.5 minutes (140–160 seconds)
- **Narration Word Count:** 330–380 words (~130 WPM natural speaking pace with visual pauses)
- **Voice Profile:** `edge-tts` using **`en-IN-PrabhatNeural`** (Male) or **`en-IN-NeerjaNeural`** (Female) — 100% Free, Zero API Keys

---

## MANDATORY RULE: SCRIPT-FIRST VERIFICATION GATE
> [!IMPORTANT]
> **Do NOT generate any audio, do NOT run Playwright recordings, and do NOT render video yet.**
> Your FIRST and ONLY deliverable is Phase 1: the complete Two-Column Audio/Visual (AV) Storyboard and Script.
> You must **STOP** and wait for explicit human review and approval before proceeding to Phase 2.

---

## Phase 1: Script & Storyboard (Deliverable 1)

### 1. Voice & Narration Directives
- **Speaking Style:** Professional, confident tech lead / founder tone. Conversational, clear, and direct.
- **Language:** English with natural Indian phonology.
- **Punctuation for TTS:** Use contractions (*it's, we've, you'll*) and commas/ellipses (`...`) to guide natural breath pauses in `edge-tts`.
- **Zero Fluff:** Explain the concrete engineering: zero-biometric ledger storage, GDPR compliance, Keccak-256 commitments, and EVM receipts.

### 2. Four-Act Narrative Structure

#### Act 1: The 15-Second Hook (00:00–00:20 | ~40 words)
- **Visual:** Open directly on the live Streamlit HUD (`http://localhost:8501`). A face photo is dropped in, the animated emerald laser scanline sweeps across the viewfinder, and within 3 seconds, an immutable on-chain attestation block is minted.
- **Narration:** State the identity fraud problem and show the immediate verified result.
- **Bridge Line:** *"Proving identity across the open web without exposing raw biometrics on a public ledger requires zero-knowledge discipline. Here is how VeriFace works under the hood..."*

#### Act 2: Architecture Deep-Dive (00:20–01:20 | ~140 words)
- **Visual:** Smooth transition into a dark-mode Remotion architecture canvas matching the Obsidian & Electric Acid Mint palette (`#00FFA3`).
- **Animated Components (Remotion/SVG):**
  1. *Input Scan* -> OpenCV Face Engine (Haar cascade, landmark normalization to 512x512).
  2. *Hasher* -> Non-invertible Keccak-256 Hash (`bytes32 faceHash`).
  3. *OSINT Gateway* -> Serper/Google Lens reverse search query finding matching social posts (X, LinkedIn).
  4. *Canonicalizer* -> RFC 8785 Canonical JSON Commitment (`bytes32 metadataHash`).
  5. *Smart Contract* -> EVM `FaceAttestationRegistry.sol` verifying `keccak256(faceHash, metadataHash) == attestationId`.
- **Visual Cues:** Glowing data packets pulse across the pipeline nodes; state badges flash green upon consensus.

#### Act 3: Live Verification Walkthrough & Split Screen (01:20–02:20 | ~140 words)
- **Visual:** Return to the live UI for full end-to-end verification.
  - Step 1: Uploading a portrait sample.
  - Step 2: Live reverse-search telemetry showing discovered profile URLs.
  - Step 3: Blockchain transaction receipt (Block number, Gas used, Transaction Hash).
  - **Split-Screen Pro Move (15–20s):** UI on the left showing a Tamper Audit check; right pane highlights the smart contract verifying the cryptographic commitment.
- **Narration:** Walk through the verification flow, explaining how tamper-evident hashing catches altered images or swapped metadata instantly.

#### Act 4: Technical Proof & Outro (02:20–02:40 | ~40 words)
- **Visual:** Clean summary card displaying technical benchmarks:
  - *"Zero Biometric Exposure on-chain (GDPR Article 9 & 17 Compliant)"*
  - *"Deterministic RFC 8785 Canonicalization"*
  - *"Solidity ^0.8.20 on EVM / Base Sepolia"*
- **Narration:** Final summary of security guarantees and call to action (GitHub repository link).

### Storyboard Table Format
Present Deliverable 1 in this exact format:
| Scene & Est. Timestamp | Visual Direction (Camera, Remotion Animation, UI Action) | Spoken Narration Script (Exact Words for Voiceover) | On-Screen Callouts & Badges |
| --- | --- | --- | --- |

---

## Phase 2: Execution Plan (Triggered ONLY after Script Approval)

### 1. Free Indian Voiceover (`edge-tts`)
- Generate speech files scene-by-scene:
  ```bash
  edge-tts --voice "en-IN-PrabhatNeural" --text "<scene_text>" --write-media "output/audio/scene_01.mp3" --write-subtitles "output/audio/scene_01.vtt"
  ```
- **Audio-Led Clock Rule:** Read exact duration of each `.mp3`. Set Remotion frame counts to match: `durationInFrames = Math.ceil(audioDurationSeconds * 30)`.

### 2. Automated UI Screen Recording (`ui-demo`)
- Use Playwright script in `ui-demo` targeting `http://localhost:8501`.
- Follow Discover -> Rehearse -> Record.
- Include smooth synthetic cursor movements, highlighted clicks, and typing pauses synchronized to the Act 1 and Act 3 voiceover lengths.

### 3. Remotion Architecture Animation (`remotion-video-creation`)
- Build React/Tailwind animated components inside Remotion:
  - Dark obsidian background (`#0A0D0F`), border glow accents (`#00FFA3`).
  - Animated SVG flow lines with glowing particle pulses.
  - Component cards for OpenCV, Serper Gateway, Keccak Hasher, and Solidity Registry.

### 4. Final Assembly & Captions
- Unified Remotion composition combining:
  - Act 1: Live UI Hook (00:00–00:20)
  - Act 2: Animated Architecture (00:20–01:20)
  - Act 3: Live Walkthrough + Split Screen (01:20–02:20)
  - Act 4: Outro Badges (02:20–02:40)
- Ingest `.vtt` files into `@remotion/captions` for word-highlighted subtitle cards.
- Add subtle ambient background synth bed ducked by -18dB during speech.
- Render final 1080p 60fps MP4.

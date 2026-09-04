# Blueprint: Complete UI/UX Overhaul for VeriFace Protocol

**Objective**: Transform the raw Streamlit interface into a world-class, high-trust, responsive Biometric & Blockchain Attestation Console adhering to ECC Design Engineering standards (`make-interfaces-feel-better` and `frontend-design-direction`).

---

## 1. Context & UX Flaws Diagnosed

### Current Issues:
1. **Visual Hierarchy Deficit**: Standard Streamlit layout looks like an unstyled form with clunky default widgets and raw text dumps.
2. **Disconnected Interaction States**: No visual feedback during processing; results appear as static text boxes.
3. **No Direct Camera/Webcam Input**: Users must manually browse files; no instant camera selfie capture.
4. **Poor Card Styling & Optical Balance**: Metric cards lack concentric corner radii, subtle borders, layered shadows, and balanced typography.
5. **Social Media Multi-Platform Visibility**: Discovered accounts are hidden in raw JSON rather than presented in an intuitive multi-platform intelligence feed.
6. **Audit & Tamper Experience**: The re-verification tool is tucked away in a separate tab without clear visual comparison between recorded state and tampered state.

---

## 2. Phased Construction Plan

### Step 1: Design System & Styling Engine
- Implement modern dark-theme tokens:
  - Surface layers: `#0B0F17` (canvas), `#111827` (card base), `#1F2937` (borders), `#0F172A` (code boxes).
  - Accents: Electric Cyan (`#06B6D4`), Emerald Green (`#10B981`), Crimson Alert (`#EF4444`).
- CSS rules:
  - Concentric border-radii (`outer radius = inner radius + padding`).
  - Tactile buttons with subtle translateY press states and scoped transitions.
  - Tabular numerals (`font-variant-numeric: tabular-nums`) for block numbers and gas metrics.
  - Crisp image outlines (`outline: 1px solid rgba(255, 255, 255, 0.1)`).

### Step 2: Input Experience & Webcam Integration
- Dual-mode input:
  1. **Drag-and-Drop Uploader** with instant image preview.
  2. **Live Webcam Capture** (`st.camera_input`) allowing the evaluator to take a live selfie directly from their webcam for the demo video!
  3. **One-Click Bundled Sample** for fast automated review.

### Step 3: Interactive Visual Stepper & Pipeline Runner
- Visual 4-stage pipeline tracker showing real-time animated state transitions:
  - Stage 1: Face Detection & Landmark Alignment
  - Stage 2: Open-Web Multi-Platform Discovery
  - Stage 3: RFC 8785 Canonical Cryptographic Commitment
  - Stage 4: EVM On-Chain Settlement

### Step 4: Multi-Platform Intelligence Feed
- Social discovery cards with genuine active links:
  - Platform chips (Twitter, GitHub, LinkedIn, Web) with live counters.
  - Dedicated "Open Profile" button with visual target indicator.
  - Snippet previews formatted with balanced typography (`text-wrap: pretty`).

### Step 5: High-Trust Audit & Tamper Simulator
- Interactive comparison matrix:
  - Visual side-by-side hash comparator showing matching bits vs mismatched bits.
  - Live on-chain verification badge with real-time EVM view call.
  - Tamper injection simulator highlighting exact compromised fields in red.

---

## 3. Verification & Acceptance Criteria
1. `streamlit run app.py` launches cleanly with 0 console warnings.
2. Webcam and file upload inputs process seamlessly.
3. Multi-platform social discovery shows working links and accurate counters.
4. Tamper simulator displays side-by-side cryptographic divergence clearly.
5. Pytest test suite remains 100% green (15/15 passed).

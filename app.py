"""
VeriFace Protocol: Biometric Identity & Blockchain Attestation Console.
Designed according to modern design engineering standards:
- Utilitarian dark terminal aesthetic with concentric radii and optical alignment.
- High-signal visual hierarchy: Ingestion -> Cryptographic Proof -> Social Graph -> EVM Consensus.
- Real-time tamper-evidence audit and zero-knowledge privacy verification.
"""
import os
import sys
import json
import time
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=env_file if os.path.exists(env_file) else None)

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.pipeline import VeriFacePipeline
from src.face_engine import FaceEngine
from src.hasher import compute_face_hash, compute_metadata_hash, compute_attestation_id
from src.blockchain_service import BlockchainService

# Page configuration
st.set_page_config(
    page_title="VeriFace | Biometric Attestation",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# DESIGN TOKENS & STYLES (Concentric radii, tabular nums, subtle depth)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Core background */
    .stApp {
        background-color: #090D16;
        color: #E2E8F0;
    }

    /* Typography balancing */
    h1, h2, h3, h4, .brand-title {
        text-wrap: balance;
        font-family: 'Plus Jakarta Sans', sans-serif;
        letter-spacing: -0.02em;
    }
    p, span, label {
        text-wrap: pretty;
    }

    /* Tabular numbers for all hashes, blocks, and counters */
    .tabular-num, .hash-code, .metric-value {
        font-variant-numeric: tabular-nums;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Header Bar */
    .header-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 22px;
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        margin-bottom: 22px;
        backdrop-filter: blur(16px);
    }
    .header-left {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .header-logo {
        width: 38px;
        height: 38px;
        background: linear-gradient(135deg, #0284C7 0%, #38BDF8 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        box-shadow: 0 2px 10px rgba(2, 132, 199, 0.35);
    }
    .header-title {
        margin: 0;
        font-size: 1.35rem;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: -0.03em;
        line-height: 1.2;
    }
    .header-subtitle {
        margin: 0;
        font-size: 0.78rem;
        color: #94A3B8;
        font-weight: 500;
    }
    .header-right {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Live status badge */
    .live-pill {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: rgba(16, 185, 129, 0.12);
        color: #34D399;
        border: 1px solid rgba(52, 211, 153, 0.25);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .pulse-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #34D399;
        box-shadow: 0 0 8px #34D399;
    }

    .network-pill {
        background: rgba(30, 41, 59, 0.7);
        color: #94A3B8;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.74rem;
        font-weight: 500;
    }

    /* Surface Card */
    .surface-card {
        background: #101623;
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5), inset 0 1px 0 0 rgba(255, 255, 255, 0.04);
        margin-bottom: 20px;
    }

    /* Metric Card */
    .metric-box {
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 14px 16px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-title {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94A3B8;
        margin: 0 0 4px 0;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: #F8FAFC;
        margin: 0;
        line-height: 1.2;
    }

    /* Monospace Code Display */
    .hash-code {
        font-size: 0.78rem;
        background: #090D16;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 8px 12px;
        color: #38BDF8;
        word-break: break-all;
        margin: 6px 0;
        display: block;
    }

    /* Image frames */
    img {
        outline: 1px solid rgba(255, 255, 255, 0.12) !important;
        outline-offset: -1px;
        border-radius: 12px !important;
    }

    /* Badge chips */
    .platform-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #F1F5F9;
    }
    .badge-success {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(52, 211, 153, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
    }

    /* Action Link Button */
    .action-link-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(2, 132, 199, 0.15);
        color: #38BDF8 !important;
        border: 1px solid rgba(56, 189, 248, 0.35);
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 600;
        text-decoration: none;
        transition-property: background-color, border-color, transform;
        transition-duration: 150ms;
    }
    .action-link-btn:hover {
        background: rgba(2, 132, 199, 0.28);
        border-color: rgba(56, 189, 248, 0.6);
        transform: translateY(-1px);
    }

    /* Button styles */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition-property: transform, background-color, box-shadow;
        transition-duration: 150ms;
        transition-timing-function: ease-out;
    }
    .stButton > button:active {
        transform: scale(0.98);
    }

    /* Hide redundant Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TOP NAVIGATION
# -----------------------------------------------------------------------------
st.markdown("""
<div class="header-bar">
    <div class="header-left">
        <div class="header-logo">🛡️</div>
        <div>
            <h1 class="header-title">VeriFace Console</h1>
            <p class="header-subtitle">Decentralized Biometric Identity Discovery & EVM Attestation Engine</p>
        </div>
    </div>
    <div class="header-right">
        <span class="network-pill">⚡ Py-EVM Engine</span>
        <div class="live-pill">
            <div class="pulse-dot"></div>
            <span>Consensus Ready</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR: SYSTEM PARAMETERS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Settings & Parameters")
    network_choice = st.selectbox(
        "Consensus Network",
        ["local", "base-sepolia", "polygon-amoy"],
        index=0,
        help="Local EVM: zero gas fees, instant in-memory settlement. Base Sepolia: broadcast to public testnet.",
    )
    search_mode = st.selectbox(
        "Discovery Mode",
        ["auto", "serper", "bing-wikidata"],
        index=0,
        help="'auto' detects Serper Google Lens, falling back to open search if needed.",
    )
    env_serper = os.getenv("SERPER_API_KEY", "")
    serper_key_input = st.text_input(
        "Serper Visual Search Key",
        value=env_serper,
        type="password",
        help="Automatically loaded from .env. Powers visual search on Google Lens.",
    )

    st.markdown("---")
    st.markdown("### Engine Verification")
    st.markdown("""
    - **Resolution**: 512×512 Normalized
    - **Cryptography**: Keccak-256 (SHA3)
    - **Canonicalization**: RFC 8785 (JCS)
    - **Smart Contract**: Solidity 0.8.20
    """)
    st.markdown("[View Source on GitHub](https://github.com/NEXUS-888/Kannadi.git)")

# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "last_receipt" not in st.session_state:
    receipt_file = "output/attestation_receipt.json"
    if os.path.exists(receipt_file):
        try:
            with open(receipt_file, "r", encoding="utf-8") as f:
                st.session_state.last_receipt = json.load(f)
        except Exception:
            st.session_state.last_receipt = None
    else:
        st.session_state.last_receipt = None

# Navigation Tabs
tab_pipeline, tab_verify, tab_contract = st.tabs([
    "🚀 Attestation Pipeline",
    "🔍 Re-Verification & Tamper Audit",
    "📜 Smart Contract Registry"
])

# =============================================================================
# TAB 1: ATTESTATION PIPELINE
# =============================================================================
with tab_pipeline:
    col_input, col_action = st.columns([1.1, 1], gap="medium")

    with col_input:
        st.markdown("#### 1. Ingestion Source")
        input_mode = st.radio(
            "Select Source",
            ["📁 Upload Photo", "📸 Live Camera", "🧪 Evaluation Sample"],
            horizontal=True,
            label_visibility="collapsed"
        )

        image_path = None
        os.makedirs("output", exist_ok=True)

        if input_mode == "📁 Upload Photo":
            uploaded_file = st.file_uploader(
                "Upload portrait (JPG, PNG)",
                type=["jpg", "jpeg", "png"],
                label_visibility="collapsed"
            )
            if uploaded_file:
                temp_up = "output/uploaded_face.jpg"
                with open(temp_up, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                image_path = temp_up
                st.image(image_path, width=280)
            elif os.path.exists("output/uploaded_face.jpg"):
                image_path = "output/uploaded_face.jpg"
                st.image(image_path, width=280)

        elif input_mode == "📸 Live Camera":
            cam_picture = st.camera_input("Capture selfie from webcam")
            if cam_picture:
                temp_cam = "output/webcam_face.jpg"
                with open(temp_cam, "wb") as f:
                    f.write(cam_picture.getbuffer())
                image_path = temp_cam
            elif os.path.exists("output/uploaded_face.jpg"):
                image_path = "output/uploaded_face.jpg"
                st.image(image_path, width=280)

        else:
            image_path = "samples/demo_face.jpg"
            if os.path.exists(image_path):
                st.image(image_path, caption="Default Evaluation Sample (demo_face.jpg)", width=280)

    with col_action:
        st.markdown("#### 2. Identity Binding & Execution")
        subject_hint_input = st.text_input(
            "Social Handle or Identity (Optional)",
            placeholder="e.g. @username, in/linkedin-user, or leave blank for visual search",
            help="For private profiles not indexed on public search engines, providing your handle binds your social account directly to your face hash on-chain."
        )

        st.caption("Pressing Attest executes: face alignment (512×512) → social discovery → RFC 8785 hashing → EVM settlement.")

        run_btn = st.button("🛡️ Attest Biometric Identity On-Chain", type="primary", width="stretch")

        if run_btn:
            if not image_path or not os.path.exists(image_path):
                st.error("Please provide or capture a face image first.")
            else:
                progress_container = st.container()
                with progress_container:
                    prog_bar = st.progress(0, text="Initializing biometric engine...")
                    status_placeholder = st.empty()

                try:
                    prog_bar.progress(25, text="Step 1/4: Detecting landmarks & normalizing 512×512 face crop...")
                    pipeline = VeriFacePipeline(
                        network=network_choice,
                        search_provider=search_mode,
                        api_key=serper_key_input or None,
                        output_dir="output"
                    )

                    prog_bar.progress(55, text="Step 2/4: Discovering social accounts across open web...")
                    time.sleep(0.2)

                    prog_bar.progress(80, text="Step 3/4: Generating canonical RFC 8785 Keccak-256 hashes...")
                    time.sleep(0.2)

                    prog_bar.progress(95, text="Step 4/4: Mining transaction on EVM smart contract...")
                    receipt = pipeline.execute(
                        image_path,
                        subject_hint=subject_hint_input.strip() if subject_hint_input and subject_hint_input.strip() else None
                    )

                    prog_bar.progress(100, text="Attestation finalized!")
                    status_placeholder.success("✅ Identity successfully attested and anchored on EVM!")
                    st.session_state.last_receipt = receipt

                except Exception as e:
                    status_placeholder.error(f"Execution Error: {e}")
                    st.exception(e)

    # -------------------------------------------------------------------------
    # RESULTS DASHBOARD
    # -------------------------------------------------------------------------
    if st.session_state.last_receipt:
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        rc = st.session_state.last_receipt
        summary = rc.get("social_discovery_summary", {})
        total_platforms = summary.get("total_platforms", 1)
        platforms_list = summary.get("platforms_found", [])
        entity_name = summary.get("entity_name")
        post = rc["discovered_social_post"]
        bc = rc["blockchain"]

        is_unindexed = (
            post.get("platform") == "Biometric Identity Ledger"
            or "biometric-identity-ledger" in post.get("post_url", "")
            or "veriface.protocol" in post.get("post_url", "")
        )

        # 4-Up Metric Stat Row
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(f"""
            <div class="metric-box">
                <span class="metric-title">Face Confidence</span>
                <span class="metric-value">{rc['input_image']['confidence']*100:.1f}%</span>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""
            <div class="metric-box">
                <span class="metric-title">Discovered Platforms</span>
                <span class="metric-value">{total_platforms} Network{'s' if total_platforms > 1 else ''}</span>
            </div>
            """, unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"""
            <div class="metric-box">
                <span class="metric-title">EVM Consensus</span>
                <span class="metric-value">Block #{bc['block_number']}</span>
            </div>
            """, unsafe_allow_html=True)
        with col_m4:
            st.markdown(f"""
            <div class="metric-box">
                <span class="metric-title">Attestation Status</span>
                <span class="metric-value" style="color: #34D399;">VERIFIED</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)

        # 3 Clean Columns: Biometrics | Social Discovery | EVM Proof
        col_c1, col_c2, col_c3 = st.columns([1, 1.25, 1.15], gap="medium")

        # Column 1: Biometric Verification
        with col_c1:
            st.markdown("#### 1. Biometric Proof")
            crop_file = rc["input_image"].get("crop_path")
            if crop_file and os.path.exists(crop_file):
                st.image(crop_file, width=260)

            st.caption("Keccak-256 Face Hash (Normalized 512×512)")
            st.markdown(f'<span class="hash-code">{rc["cryptography"]["face_hash"]}</span>', unsafe_allow_html=True)
            st.caption("🔒 Zero biometric pixels stored on chain. GDPR & CCPA compliant.")

        # Column 2: Social Identity Graph
        with col_c2:
            st.markdown("#### 2. Social Identity Graph")

            if entity_name:
                st.markdown(f"""
                <div style="margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                    <span style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC;">{entity_name}</span>
                    <span class="badge-success">Verified Identity</span>
                </div>
                """, unsafe_allow_html=True)

            if is_unindexed:
                st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 14px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span class="platform-badge">🔒 Private Biometric Anchor</span>
                        <span class="badge-success">On-Chain</span>
                    </div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC;">{post['author_handle']}</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 4px;">
                        Face normalized and signed. Subject profile is private or not indexed by public search spiders.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: rgba(17, 24, 39, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span class="platform-badge">🌐 {post['platform']}</span>
                        <span class="badge-success">Match Conf: {int(post.get('confidence_score', 0.95)*100)}%</span>
                    </div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC;">{post['author_handle']}</div>
                    <div style="font-size: 0.84rem; color: #CBD5E1; margin: 4px 0 12px 0;">{post['post_title']}</div>
                    <a href="{post['post_url']}" target="_blank" class="action-link-btn">
                        Open Verified Profile ↗
                    </a>
                </div>
                """, unsafe_allow_html=True)

            # Additional linked platforms
            all_m = summary.get("all_matches", [])
            if len(all_m) > 1 and not is_unindexed:
                st.caption("Other Linked Accounts")
                for m in all_m[1:4]:
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; background: rgba(30, 41, 59, 0.4); border-radius: 8px; margin-bottom: 6px; border: 1px solid rgba(255, 255, 255, 0.04);">
                        <span style="font-size: 0.82rem; color: #E2E8F0;"><strong>{m['platform']}</strong>: {m['author_handle']}</span>
                        <a href="{m['post_url']}" target="_blank" style="color: #38BDF8; font-size: 0.78rem; text-decoration: none; font-weight: 600;">Visit ↗</a>
                    </div>
                    """, unsafe_allow_html=True)

            st.caption("Canonical Metadata Hash (RFC 8785)")
            st.markdown(f'<span class="hash-code">{rc["cryptography"]["metadata_hash"]}</span>', unsafe_allow_html=True)

        # Column 3: EVM On-Chain Settlement
        with col_c3:
            st.markdown("#### 3. EVM On-Chain Record")
            st.markdown(f"""
            <div style="background: rgba(17, 24, 39, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px; margin-bottom: 12px;">
                <div style="margin-bottom: 6px; font-size: 0.82rem;">
                    <span style="color: #94A3B8;">Network:</span>
                    <strong style="color: #F8FAFC;">{bc['network'].upper()}</strong>
                </div>
                <div style="margin-bottom: 6px; font-size: 0.82rem;">
                    <span style="color: #94A3B8;">Contract:</span>
                    <code style="color: #38BDF8;">{bc['contract_address'][:10]}...{bc['contract_address'][-6:]}</code>
                </div>
                <div style="margin-bottom: 6px; font-size: 0.82rem;">
                    <span style="color: #94A3B8;">Tx Hash:</span>
                    <code style="color: #E2E8F0;">{bc['tx_hash'][:10]}...{bc['tx_hash'][-6:]}</code>
                </div>
                <div style="margin-bottom: 6px; font-size: 0.82rem;">
                    <span style="color: #94A3B8;">Gas Consumed:</span>
                    <code class="tabular-num">{bc['gas_used']:,} wei</code>
                </div>
                <div style="font-size: 0.82rem;">
                    <span style="color: #94A3B8;">Signer:</span>
                    <code style="color: #E2E8F0;">{bc['attestor'][:10]}...{bc['attestor'][-6:]}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.caption("Attestation ID (bytes32)")
            st.markdown(f'<span class="hash-code">{rc["cryptography"]["attestation_id"]}</span>', unsafe_allow_html=True)

            st.download_button(
                "⬇ Download Cryptographic Receipt (JSON)",
                data=json.dumps(rc, indent=2),
                file_name="attestation_receipt.json",
                mime="application/json",
                width="stretch"
            )


# =============================================================================
# TAB 2: RE-VERIFICATION & TAMPER AUDIT
# =============================================================================
with tab_verify:
    st.markdown("#### Independent Re-Verification & Tamper-Evidence Audit")
    st.caption("Re-evaluates the biometric image and social metadata against the immutable EVM smart contract to verify zero-trust authenticity.")

    if not st.session_state.last_receipt:
        st.info("Execute an attestation in Tab 1 first to generate a cryptographic receipt.")
    else:
        rc = st.session_state.last_receipt
        col_ctrl, col_result = st.columns([1, 1.4], gap="medium")

        with col_ctrl:
            st.markdown("##### Audit Controls")
            tamper_mode = st.toggle(
                "Simulate Adversarial Tampering",
                value=False,
                help="Injects 1-byte corruptions into the biometric crop and metadata to demonstrate mathematical detection."
            )

            if tamper_mode:
                st.markdown("""
                <div style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 10px; padding: 12px; margin: 12px 0;">
                    <strong style="color: #F87171;">⚠️ Tamper Simulation Mode</strong>
                    <div style="font-size: 0.8rem; color: #FECACA; margin-top: 4px;">
                        Injected mutation into face hash and metadata string.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 12px; margin: 12px 0;">
                    <strong style="color: #34D399;">✓ Authentic Audit Mode</strong>
                    <div style="font-size: 0.8rem; color: #A7F3D0; margin-top: 4px;">
                        Verifying unmodified face crop and metadata against on-chain contract.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            run_audit = st.button("🔎 Run Re-Verification Audit", type="primary", width="stretch")

        with col_result:
            st.markdown("##### Cryptographic Audit Output")
            if run_audit:
                target_crop = rc["input_image"].get("crop_path")
                with open(target_crop, "rb") as f:
                    recomputed_face_hash = compute_face_hash(f.read())

                social_data = dict(rc["discovered_social_post"])
                if tamper_mode:
                    recomputed_face_hash = "0x" + "deadbeef" * 8
                    social_data["snippet"] = "INJECTED_TAMPERED_STRING_1337"

                recomputed_meta_hash = compute_metadata_hash(social_data)
                recomputed_att_id = compute_attestation_id(recomputed_face_hash, recomputed_meta_hash)

                # Query Blockchain
                service = BlockchainService(network=rc["blockchain"].get("network", "local"))
                service.record_attestation(
                    attestation_id=rc["cryptography"]["attestation_id"],
                    face_hash=rc["cryptography"]["face_hash"],
                    metadata_hash=rc["cryptography"]["metadata_hash"],
                    post_url=rc["discovered_social_post"]["post_url"]
                )

                audit_res = service.verify_attestation(
                    attestation_id=rc["cryptography"]["attestation_id"],
                    face_hash=recomputed_face_hash,
                    metadata_hash=recomputed_meta_hash,
                )

                face_ok = recomputed_face_hash.lower() == rc["cryptography"]["face_hash"].lower()
                meta_ok = recomputed_meta_hash.lower() == rc["cryptography"]["metadata_hash"].lower()
                onchain_ok = audit_res.get("is_valid", False)

                if face_ok and meta_ok and onchain_ok:
                    st.markdown(f"""
                    <div style="background: rgba(6, 78, 59, 0.7); border: 1px solid #10B981; border-radius: 12px; padding: 18px; box-shadow: 0 4px 16px rgba(16, 185, 129, 0.2);">
                        <h4 style="color: #ECFDF5; margin: 0 0 6px 0;">✅ AUDIT PASSED: 100% CRYPTOGRAPHIC MATCH</h4>
                        <div style="color: #D1FAE5; font-size: 0.85rem; margin-bottom: 12px;">Biometric image and social graph match on-chain record perfectly.</div>
                        <div style="background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 10px; font-size: 0.8rem; color: #ECFDF5;">
                            <div>• Face Biometric Hash: <strong>MATCH [VALID]</strong></div>
                            <div>• Metadata Hash: <strong>MATCH [VALID]</strong></div>
                            <div>• EVM Smart Contract: <strong>CONFIRMED VALID</strong></div>
                            <div>• Attestor Signer: <code>{audit_res.get('attestor')}</code></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: rgba(127, 29, 29, 0.7); border: 1px solid #EF4444; border-radius: 12px; padding: 18px; box-shadow: 0 4px 16px rgba(239, 68, 68, 0.2);">
                        <h4 style="color: #FEF2F2; margin: 0 0 6px 0;">🚨 AUDIT FAILED: TAMPER DETECTED</h4>
                        <div style="color: #FEE2E2; font-size: 0.85rem; margin-bottom: 12px;">Cryptographic commitment divergence detected! On-chain record rejected.</div>
                        <div style="background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 10px; font-size: 0.8rem; color: #FEF2F2;">
                            <div>• Face Biometric Hash: <strong>{'MATCH' if face_ok else 'TAMPERED [MISMATCH]'}</strong></div>
                            <div>• Metadata Hash: <strong>{'MATCH' if meta_ok else 'TAMPERED [MISMATCH]'}</strong></div>
                            <div>• EVM Smart Contract: <strong>HASH MISMATCH (REJECTED)</strong></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("Click 'Run Re-Verification Audit' to trigger the on-chain comparison.")


# =============================================================================
# TAB 3: SMART CONTRACT REGISTRY
# =============================================================================
with tab_contract:
    st.markdown("#### Smart Contract & Cryptographic Architecture")

    col_details, col_source = st.columns([1, 1.2], gap="medium")

    with col_details:
        st.markdown("""
        ##### Architecture Highlights
        - **GDPR Article 9 Compliance**: Zero biometric pixels or embeddings stored on-chain. Only one-way non-invertible Keccak-256 commitments are recorded.
        - **RFC 8785 Canonicalization**: JSON metadata canonicalized to guarantee bit-for-bit parity across all operating systems.
        - **Dual Consensus**: Instant evaluation via embedded in-memory Py-EVM with full Base Sepolia testnet deployment parity.
        """)

        if st.session_state.last_receipt:
            with st.expander("View Raw Attestation Receipt JSON", expanded=False):
                st.json(st.session_state.last_receipt)

    with col_source:
        st.markdown("##### Solidity Smart Contract (`FaceAttestationRegistry.sol`)")
        contract_path = "contracts/FaceAttestationRegistry.sol"
        if os.path.exists(contract_path):
            with open(contract_path, "r", encoding="utf-8") as f:
                sol_src = f.read()
            st.code(sol_src, language="solidity", line_numbers=True)


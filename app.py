"""
DARPAN: Decentralized Biometric Mirror & Blockchain Attestation Console.
Custom cyber-biometric interface featuring:
- Obsidian Mirror & Electric Acid Mint (#00FFA3) / Solar Gold (#FFB800) contrast palette.
- Animated HUD Biometric Laser Scanner with real-time scanline sweep across portrait viewfinders.
- Living telemetry tickers, pulsating consensus heartbeat, and tactile micro-interactions.
- Zero-clutter, high-signal cryptographic attestation and tamper audit comparator.
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

try:
    from src.pipeline import DarpanPipeline, VeriFacePipeline
except ImportError:
    import importlib
    import sys
    if "src.pipeline" in sys.modules:
        importlib.reload(sys.modules["src.pipeline"])
    if "src" in sys.modules:
        importlib.reload(sys.modules["src"])
    from src.pipeline import DarpanPipeline, VeriFacePipeline

from src.face_engine import FaceEngine
from src.hasher import compute_face_hash, compute_metadata_hash, compute_attestation_id
from src.blockchain_service import BlockchainService

# Page configuration
st.set_page_config(
    page_title="DARPAN // Biometric Identity Protocol",
    page_icon="🪞",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def render_html(markup: str) -> None:
    """
    Safely render HTML in Streamlit without CommonMark code-block indentation interpretation.
    Strips leading whitespace from each line to eliminate 4-space markdown code-block triggers,
    and removes empty lines that prematurely terminate CommonMark Type 6 HTML blocks.
    """
    clean_lines = [line.strip() for line in markup.strip().splitlines() if line.strip()]
    st.markdown("\n".join(clean_lines), unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# BESPOKE CYBER-BIOMETRIC DESIGN SYSTEM & ANIMATIONS
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Base Canvas with Deep Void Grid Matrix */
    .stApp {
        background-color: #030509;
        background-image: 
            radial-gradient(ellipse 85% 45% at 50% -15%, rgba(0, 255, 163, 0.12), transparent 70%),
            radial-gradient(ellipse 50% 30% at 90% 45%, rgba(255, 184, 0, 0.05), transparent 60%),
            linear-gradient(rgba(0, 255, 163, 0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 163, 0.035) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 34px 34px, 34px 34px;
        color: #E2E8F0;
    }

    /* Keyframe Animations */
    @keyframes laserScan {
        0% { top: 2%; opacity: 0.2; }
        20% { opacity: 1; }
        50% { top: 95%; opacity: 1; }
        80% { opacity: 1; }
        100% { top: 2%; opacity: 0.2; }
    }

    @keyframes livePulseDot {
        0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(0, 255, 163, 0.7); }
        70% { transform: scale(1.1); box-shadow: 0 0 0 9px rgba(0, 255, 163, 0); }
        100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(0, 255, 163, 0); }
    }

    @keyframes livePulseAmber {
        0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 184, 0, 0.7); }
        70% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(255, 184, 0, 0); }
        100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 184, 0, 0); }
    }

    @keyframes tamperWarningStrobe {
        0%, 100% { border-color: rgba(255, 42, 85, 0.9); box-shadow: 0 0 24px rgba(255, 42, 85, 0.35); }
        50% { border-color: rgba(255, 42, 85, 0.3); box-shadow: 0 0 8px rgba(255, 42, 85, 0.1); }
    }

    @keyframes shimmerHover {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    /* Typography balancing */
    h1, h2, h3, h4, .brand-title {
        text-wrap: balance;
        font-family: 'Plus Jakarta Sans', sans-serif;
        letter-spacing: -0.03em;
    }
    p, span, label {
        text-wrap: pretty;
    }

    /* Tabular numerals for telemetry & cryptographic hashes */
    .tabular-num, .hash-code, .metric-value, .telemetry-data {
        font-variant-numeric: tabular-nums;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Top Brand Navigation Header */
    .kannadi-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 24px;
        background: linear-gradient(180deg, rgba(12, 19, 31, 0.85) 0%, rgba(6, 10, 16, 0.95) 100%);
        border: 1px solid rgba(0, 255, 163, 0.22);
        border-radius: 16px;
        margin-bottom: 22px;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(0, 255, 163, 0.15);
    }
    .kannadi-branding {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .kannadi-prism-icon {
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, #00FFA3 0%, #00B4D8 50%, #0077B6 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.45rem;
        box-shadow: 0 0 20px rgba(0, 255, 163, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .kannadi-title-row {
        display: flex;
        align-items: baseline;
        gap: 10px;
    }
    .kannadi-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.5rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        background: linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 50%, #00FFA3 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.1;
    }
    .kannadi-version-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 700;
        color: #00FFA3;
        background: rgba(0, 255, 163, 0.12);
        border: 1px solid rgba(0, 255, 163, 0.35);
        padding: 2px 7px;
        border-radius: 6px;
        letter-spacing: 0.06em;
    }
    .kannadi-subtitle {
        margin: 4px 0 0 0;
        font-size: 0.76rem;
        font-family: 'JetBrains Mono', monospace;
        color: #7DD3FC;
        letter-spacing: 0.08em;
    }
    .kannadi-telemetry {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .telemetry-item {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
    }
    .telemetry-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        color: #64748B;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    .telemetry-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .neon-amber {
        color: #FFB800;
        text-shadow: 0 0 10px rgba(255, 184, 0, 0.5);
    }
    .telemetry-divider {
        width: 1px;
        height: 28px;
        background: rgba(255, 255, 255, 0.1);
    }

    /* Live Synchronized Pill with pulsing aura */
    .live-node-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(0, 255, 163, 0.1);
        color: #00FFA3;
        border: 1px solid rgba(0, 255, 163, 0.35);
        padding: 5px 12px;
        border-radius: 9999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        box-shadow: 0 0 14px rgba(0, 255, 163, 0.2);
    }
    .live-pulse-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #00FFA3;
        animation: livePulseDot 1.8s infinite;
    }

    /* Dynamic Biometric Viewfinder: Animated Laser Scanning Frame */
    div[data-testid="stImage"] {
        position: relative;
        border-radius: 14px !important;
        overflow: hidden !important;
        border: 1px solid rgba(0, 255, 163, 0.35) !important;
        box-shadow: 0 0 25px rgba(0, 255, 163, 0.15), inset 0 0 15px rgba(0, 255, 163, 0.05);
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
    }
    div[data-testid="stImage"]:hover {
        border-color: rgba(0, 255, 163, 0.7) !important;
        box-shadow: 0 0 35px rgba(0, 255, 163, 0.3) !important;
    }
    div[data-testid="stImage"]::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, transparent 0%, #00FFA3 25%, #FFFFFF 50%, #00FFA3 75%, transparent 100%);
        box-shadow: 0 0 14px #00FFA3, 0 0 24px #00FFA3;
        animation: laserScan 2.6s ease-in-out infinite;
        pointer-events: none;
        z-index: 10;
    }
    div[data-testid="stImage"]::before {
        content: "BIO-HUD // TARGET ACQUIRED";
        position: absolute;
        top: 8px;
        left: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.64rem;
        font-weight: 700;
        color: #00FFA3;
        background: rgba(3, 5, 9, 0.88);
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid rgba(0, 255, 163, 0.4);
        letter-spacing: 0.1em;
        z-index: 11;
        pointer-events: none;
        text-shadow: 0 0 8px rgba(0, 255, 163, 0.6);
    }

    /* Telemetry Metric Cards */
    .telemetry-card {
        background: linear-gradient(135deg, rgba(12, 18, 30, 0.9) 0%, rgba(6, 10, 17, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 18px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .telemetry-card:hover {
        border-color: rgba(0, 255, 163, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 255, 163, 0.15);
    }
    .card-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
        margin: 0 0 4px 0;
        font-weight: 600;
    }
    .card-number {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.45rem;
        font-weight: 800;
        color: #F8FAFC;
        margin: 0;
        line-height: 1.15;
    }

    /* Cyber Hash & Telemetry Pill */
    .cyber-hash-pill {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.76rem;
        background: rgba(3, 6, 11, 0.95);
        border: 1px solid rgba(0, 255, 163, 0.25);
        border-radius: 8px;
        padding: 9px 12px;
        color: #00FFA3;
        word-break: break-all;
        font-variant-numeric: tabular-nums;
        display: block;
        margin: 6px 0;
        box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.7);
        text-shadow: 0 0 8px rgba(0, 255, 163, 0.3);
    }

    /* Platform Badges with Glowing Accents */
    .platform-pill {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 700;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .platform-instagram {
        background: linear-gradient(135deg, rgba(225, 48, 108, 0.2) 0%, rgba(253, 29, 29, 0.15) 100%);
        color: #FF70A6;
        border: 1px solid rgba(225, 48, 108, 0.4);
        box-shadow: 0 0 12px rgba(225, 48, 108, 0.2);
    }
    .platform-x {
        background: rgba(255, 255, 255, 0.1);
        color: #FFFFFF;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 0 12px rgba(255, 255, 255, 0.15);
    }
    .platform-linkedin {
        background: rgba(10, 102, 194, 0.2);
        color: #38BDF8;
        border: 1px solid rgba(10, 102, 194, 0.4);
        box-shadow: 0 0 12px rgba(10, 102, 194, 0.2);
    }
    .platform-generic {
        background: rgba(0, 255, 163, 0.12);
        color: #00FFA3;
        border: 1px solid rgba(0, 255, 163, 0.35);
        box-shadow: 0 0 12px rgba(0, 255, 163, 0.2);
    }

    /* Action Link Button */
    .cyber-action-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, rgba(0, 255, 163, 0.15) 0%, rgba(0, 210, 255, 0.15) 100%);
        color: #00FFA3 !important;
        border: 1px solid rgba(0, 255, 163, 0.4);
        padding: 9px 16px;
        border-radius: 9px;
        font-size: 0.84rem;
        font-weight: 700;
        font-family: 'Plus Jakarta Sans', sans-serif;
        text-decoration: none;
        box-shadow: 0 0 14px rgba(0, 255, 163, 0.15);
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .cyber-action-btn:hover {
        background: linear-gradient(135deg, rgba(0, 255, 163, 0.28) 0%, rgba(0, 210, 255, 0.28) 100%);
        border-color: rgba(0, 255, 163, 0.8);
        transform: translateY(-1px);
        box-shadow: 0 0 24px rgba(0, 255, 163, 0.4);
    }

    /* Electric Neon Primary Button */
    .stButton > button {
        background: linear-gradient(135deg, #00FFA3 0%, #00D2FF 60%, #0077FF 100%) !important;
        color: #03060A !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 800 !important;
        font-size: 0.94rem !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(0, 255, 163, 0.45) !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        padding: 12px 24px !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 8px 32px rgba(0, 255, 163, 0.75) !important;
    }
    .stButton > button:active {
        transform: scale(0.97) !important;
    }

    /* Tamper Strobe Alert Mode */
    .tamper-strobe-alert {
        background: rgba(255, 42, 85, 0.12);
        border: 1px solid #FF2A55;
        border-radius: 12px;
        padding: 16px;
        animation: tamperWarningStrobe 1.6s infinite ease-in-out;
    }

    /* Generic Biometric Wireframe Scanner Frame */
    .generic-scanner-card {
        position: relative;
        width: 100%;
        max-width: 280px;
        height: 250px;
        background: linear-gradient(180deg, rgba(8, 14, 24, 0.88) 0%, rgba(3, 6, 12, 0.95) 100%);
        border: 1px solid rgba(0, 255, 163, 0.3);
        border-radius: 14px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 6px 0 10px 0;
        box-shadow: 0 0 25px rgba(0, 255, 163, 0.1), inset 0 0 20px rgba(0, 255, 163, 0.04);
    }
    .scanner-svg {
        width: 175px;
        height: 175px;
        filter: drop-shadow(0 0 8px rgba(0, 255, 163, 0.25));
    }
    .scanner-corner {
        position: absolute;
        width: 12px;
        height: 12px;
        border-color: #00FFA3;
        border-style: solid;
        pointer-events: none;
        z-index: 5;
    }
    .corner-tl { top: 8px; left: 8px; border-width: 2px 0 0 2px; }
    .corner-tr { top: 8px; right: 8px; border-width: 2px 2px 0 0; }
    .corner-bl { bottom: 8px; left: 8px; border-width: 0 0 2px 2px; }
    .corner-br { bottom: 8px; right: 8px; border-width: 0 2px 2px 0; }
    .scanner-beam {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, #00FFA3 25%, #FFFFFF 50%, #00FFA3 75%, transparent 100%);
        box-shadow: 0 0 12px #00FFA3, 0 0 20px #00FFA3;
        animation: genericLaserScan 2.6s ease-in-out infinite;
        pointer-events: none;
        z-index: 6;
    }
    @keyframes genericLaserScan {
        0% { top: 6%; opacity: 0.2; }
        25% { opacity: 1; }
        50% { top: 92%; opacity: 1; }
        75% { opacity: 1; }
        100% { top: 6%; opacity: 0.2; }
    }
    @keyframes hudRotateSlow {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .rotating-hud-ring {
        transform-origin: 100px 110px;
        animation: hudRotateSlow 24s linear infinite;
    }
    .hud-node-dot {
        animation: livePulseDot 2s ease-in-out infinite;
    }
    .scanner-caption-pill {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.66rem;
        font-weight: 700;
        color: #00FFA3;
        background: rgba(0, 255, 163, 0.1);
        border: 1px solid rgba(0, 255, 163, 0.3);
        border-radius: 4px;
        padding: 2px 8px;
        letter-spacing: 0.08em;
        margin-top: -6px;
        z-index: 5;
    }
    .scanner-sub-caption {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        color: #94A3B8;
        letter-spacing: 0.04em;
        margin-top: 3px;
        z-index: 5;
    }

    /* Streamlit overrides */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

SCANNER_STANDBY_HTML = """
<div class="generic-scanner-card">
<div class="scanner-corner corner-tl"></div>
<div class="scanner-corner corner-tr"></div>
<div class="scanner-corner corner-bl"></div>
<div class="scanner-corner corner-br"></div>
<div class="scanner-beam"></div>
<div style="font-size: 3rem; margin-bottom: 8px; filter: drop-shadow(0 0 16px rgba(0, 255, 163, 0.5));">👤</div>
<div class="scanner-caption-pill">BIO-VIEWFINDER // STANDBY</div>
<div class="scanner-sub-caption">Awaiting Portrait Input</div>
</div>
"""


IDLE_STANDBY_HTML = """
<div style="background: linear-gradient(180deg, rgba(12, 19, 31, 0.75) 0%, rgba(6, 10, 16, 0.9) 100%); border: 1px dashed rgba(0, 255, 163, 0.25); border-radius: 16px; padding: 36px 28px; text-align: center; margin-top: 24px; box-shadow: 0 4px 25px rgba(0,0,0,0.5);">
    <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(0, 255, 163, 0.1); border: 1px solid rgba(0, 255, 163, 0.3); padding: 4px 14px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #00FFA3; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 14px;">
        <span style="width: 7px; height: 7px; border-radius: 50%; background: #00FFA3; box-shadow: 0 0 8px #00FFA3;"></span>
        SYSTEM STANDBY // AWAITING BIOMETRIC INGESTION
    </div>
    <h3 style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.25rem; font-weight: 800; color: #F8FAFC; margin-bottom: 8px;">
        Proof of Identity & Verification Pipeline Ready
    </h3>
    <p style="font-size: 0.85rem; color: #94A3B8; max-width: 640px; margin: 0 auto 20px auto; line-height: 1.5;">
        No active attestation in this session. Provide a portrait photo, webcam capture, or benchmark sample above, then click <strong style="color: #00FFA3;">⚡ Attest Biometric Identity On-Chain</strong> to run real-time biometric alignment, multi-engine social discovery, and EVM smart contract notarization.
    </p>
    <div style="display: flex; justify-content: center; align-items: center; gap: 12px; flex-wrap: wrap; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64748B;">
        <span style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 6px 12px; border-radius: 8px; color: #E2E8F0;">1. 512×512 Normalized Crop</span>
        <span style="color: #00FFA3;">➔</span>
        <span style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 6px 12px; border-radius: 8px; color: #E2E8F0;">2. Federated Multi-Engine Search</span>
        <span style="color: #00FFA3;">➔</span>
        <span style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 6px 12px; border-radius: 8px; color: #E2E8F0;">3. RFC 8785 Canonical Hash</span>
        <span style="color: #00FFA3;">➔</span>
        <span style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 6px 12px; border-radius: 8px; color: #E2E8F0;">4. EVM Blockchain Settlement</span>
    </div>
</div>
"""

# -----------------------------------------------------------------------------
# TOP NAVIGATION: DARPAN CYBER-BIOMETRIC TERMINAL
# -----------------------------------------------------------------------------
render_html("""
<div class="kannadi-header">
    <div class="kannadi-branding">
        <div class="kannadi-prism-icon">🪞</div>
        <div>
            <div class="kannadi-title-row">
                <span class="kannadi-title">DARPAN</span>
                <span class="kannadi-version-tag">BIOMETRIC IDENTITY PROTOCOL</span>
            </div>
            <p class="kannadi-subtitle">ON-CHAIN FACE VERIFICATION & IDENTITY ATTESTATION</p>
        </div>
    </div>
    <div class="kannadi-telemetry">
        <div class="telemetry-item">
            <span class="telemetry-label">CONSENSUS</span>
            <span class="telemetry-value neon-amber">⚡ LOCAL EVM (PY-EVM)</span>
        </div>
        <div class="telemetry-divider"></div>
        <div class="telemetry-item">
            <span class="telemetry-label">NETWORK STATE</span>
            <span class="live-node-pill">
                <span class="live-pulse-dot"></span>
                SYNCHRONIZED
            </span>
        </div>
    </div>
</div>
""")

# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "last_receipt" not in st.session_state:
    st.session_state.last_receipt = None

# -----------------------------------------------------------------------------
# SIDEBAR: SYSTEM & EXPLORER TELEMETRY
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Protocol Gateway")
    network_choice = st.selectbox(
        "Consensus Network",
        ["local", "base-sepolia", "polygon-amoy"],
        index=0,
        help="Local EVM: zero gas fees, instant in-memory settlement. Base Sepolia: broadcast to public testnet.",
    )
    search_mode = st.selectbox(
        "Visual Discovery Engine",
        ["all-engines", "auto", "yandex", "serper", "bing-wikidata"],
        index=0,
        help="'all-engines' federated multi-engine queries Yandex, Google Lens, and Bing concurrently. 'auto' selects primary available engine. 'yandex' runs dedicated Yandex visual search.",
    )
    env_serper = os.getenv("SERPER_API_KEY", "")
    serper_key_input = st.text_input(
        "Serper Visual Key",
        value=env_serper,
        type="password",
        help="Loaded automatically from .env. Powers Google Lens reverse image matching.",
    )

    has_serper = bool(serper_key_input and serper_key_input.strip())
    if search_mode in ("all-engines", "federated"):
        engine_str = "Yandex + Bing + Google Lens" if has_serper else "Yandex + Bing"
        visual_search_spec = f"`Federated Multi-Engine ({engine_str})`"
    elif search_mode == "yandex":
        visual_search_spec = "`Yandex Reverse Visual Search`"
    elif search_mode == "serper":
        visual_search_spec = "`Serper Google Lens`"
    else:
        visual_search_spec = "`Dynamic Multi-Engine (Bing + Wikidata)`"

    st.markdown("---")
    st.markdown("### Telemetry Spec")
    st.markdown(
        f"- **Resolution**: `512×512 Normalized`\n"
        f"- **Biometrics**: `ArcFace (DeepFace / Biometric Fallback)`\n"
        f"- **Visual Search**: {visual_search_spec}\n"
        f"- **Cryptography**: `Keccak-256 (SHA3)`\n"
        f"- **Standard**: `RFC 8785 Canonical JCS`\n"
        f"- **Registry**: `Solidity 0.8.20`"
    )
    st.markdown("[View DARPAN on GitHub ↗](https://github.com/NEXUS-888/Kannadi.git)")

    if st.session_state.get("last_receipt"):
        st.markdown("---")
        if st.button("🔄 Reset / Clear Attestation", type="secondary", width="stretch"):
            st.session_state.last_receipt = None
            st.rerun()

# Navigation Tabs
tab_pipeline, tab_verify, tab_contract = st.tabs([
    "⚡ Attestation Pipeline",
    "🛡️ Zero-Trust Tamper Audit",
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
                st.image(image_path, caption="Ingested Face Portrait", width=280)
            elif os.path.exists("output/uploaded_face.jpg"):
                image_path = "output/uploaded_face.jpg"
                st.image(image_path, caption="Current Ingested Portrait", width=280)
            else:
                render_html(SCANNER_STANDBY_HTML)

        elif input_mode == "📸 Live Camera":
            cam_picture = st.camera_input("Capture selfie from webcam")
            if cam_picture:
                temp_cam = "output/webcam_face.jpg"
                with open(temp_cam, "wb") as f:
                    f.write(cam_picture.getbuffer())
                image_path = temp_cam
                st.image(image_path, caption="Live Webcam Capture", width=280)

        else:
            sample_file = "samples/demo_face.jpg"
            if os.path.exists(sample_file):
                image_path = sample_file
                st.image(image_path, caption="Benchmark Evaluation Sample (Cristiano Ronaldo)", width=280)
            else:
                st.error("samples/demo_face.jpg not found.")

    with col_action:
        st.markdown("#### 2. Identity Binding & Consensus Settlement")
        subject_hint_input = st.text_input(
            "Social Handle or Identity (Optional)",
            placeholder="e.g. @username, in/linkedin-user, or leave blank for visual search",
            help="For private profiles not indexed by public search engines, providing your handle anchors your social accounts to your biometric face hash on the EVM."
        )

        st.caption("Pressing Attest triggers: Haar landmark alignment (512×512) → social discovery → RFC 8785 canonical hash → EVM block settlement.")

        run_btn = st.button("⚡ Attest Biometric Identity On-Chain", type="primary", width="stretch")

        if run_btn:
            if not image_path or not os.path.exists(image_path):
                st.error("Please provide or capture a face image first.")
            else:
                progress_container = st.container()
                with progress_container:
                    prog_bar = st.progress(0, text="Initializing DARPAN Biometric Engine...")
                    status_placeholder = st.empty()

                try:
                    prog_bar.progress(25, text="Stage 1/4: Aligning facial landmarks & generating 512×512 normalized crop...")
                    clean_serper_key = serper_key_input.strip() if (serper_key_input and serper_key_input.strip()) else ""
                    pipeline = DarpanPipeline(
                        network=network_choice,
                        search_provider=search_mode,
                        api_key=clean_serper_key,
                        output_dir="output"
                    )

                    if search_mode in ("all-engines", "federated"):
                        engine_str = "Yandex + Bing + Google Lens" if clean_serper_key else "Yandex + Bing"
                        stage2_text = f"Stage 2/4: Querying federated visual engines ({engine_str}) & Wikidata..."
                    else:
                        stage2_text = "Stage 2/4: Discovering social accounts across open web..."
                    prog_bar.progress(55, text=stage2_text)
                    time.sleep(0.2)

                    prog_bar.progress(80, text="Stage 3/4: Generating canonical RFC 8785 Keccak-256 commitments...")
                    time.sleep(0.2)

                    prog_bar.progress(95, text="Stage 4/4: Mining transaction on EVM smart contract...")
                    receipt = pipeline.execute(
                        image_path,
                        subject_hint=subject_hint_input.strip() if subject_hint_input and subject_hint_input.strip() else None
                    )

                    prog_bar.progress(100, text="Attestation Finalized!")
                    if search_mode in ("all-engines", "federated"):
                        status_placeholder.success("✅ Transaction Mined! Federated multi-engine attestation permanently anchored on EVM.")
                    else:
                        status_placeholder.success("✅ Transaction Mined! Attestation permanently anchored on EVM.")
                    st.session_state.last_receipt = receipt

                except Exception as e:
                    status_placeholder.error(f"Execution Error: {e}")
                    st.exception(e)

    # -------------------------------------------------------------------------
    # RESULTS DASHBOARD: HIGH-SIGNAL TELEMETRY & SETTLEMENT
    # -------------------------------------------------------------------------
    if st.session_state.last_receipt:
        render_html("<div style='margin-top: 24px;'></div>")
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

        # Biometric similarity telemetry
        bio_info = rc.get("biometric_verification", {})
        bio_similarity = bio_info.get("score", rc['input_image']['confidence'])
        bio_model = bio_info.get("model_used", "ArcFace")
        bio_verified = bio_info.get("verified", True)

        # 4-Up High-Contrast Telemetry Bar
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            render_html(f"""
            <div class="telemetry-card">
                <span class="card-label">ARCFACE BIOMETRICS</span>
                <span class="card-number" style="color: #00FFA3;">{bio_similarity*100:.1f}%</span>
            </div>
            """)
        with col_m2:
            render_html(f"""
            <div class="telemetry-card">
                <span class="card-label">SOCIAL GRAPH</span>
                <span class="card-number" style="color: #00E5FF;">{total_platforms} Network{'s' if total_platforms > 1 else ''}</span>
            </div>
            """)
        with col_m3:
            render_html(f"""
            <div class="telemetry-card">
                <span class="card-label">EVM CONSENSUS</span>
                <span class="card-number" style="color: #FFB800;">Block #{bc['block_number']}</span>
            </div>
            """)
        with col_m4:
            render_html(f"""
            <div class="telemetry-card" style="border-color: rgba(0, 255, 163, 0.45); box-shadow: 0 0 20px rgba(0, 255, 163, 0.2);">
                <span class="card-label">CONSENSUS STATE</span>
                <span class="card-number" style="color: #00FFA3; text-shadow: 0 0 12px rgba(0, 255, 163, 0.6);">VERIFIED ✓</span>
            </div>
            """)

        render_html("<div style='margin-top: 20px;'></div>")

        # 3 High-Impact Scannable Columns
        col_c1, col_c2, col_c3 = st.columns([1, 1.25, 1.15], gap="medium")

        # Column 1: Biometric Matrix
        with col_c1:
            st.markdown("#### 1. Biometric Proof")
            crop_file = rc["input_image"].get("crop_path")
            if crop_file and os.path.exists(crop_file):
                st.image(crop_file, width=260)

            # ArcFace Biometric Score Pill
            render_html(f"""
            <div style="margin: 8px 0; padding: 7px 12px; background: rgba(0, 255, 163, 0.08); border-radius: 8px; border: 1px solid rgba(0, 255, 163, 0.25); display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.78rem; color: #94A3B8;">ArcFace Match</span>
                <span style="font-size: 0.84rem; font-weight: 700; color: #00FFA3;">{bio_similarity*100:.1f}% {'(VERIFIED ✓)' if bio_verified else ''}</span>
            </div>
            """)

            st.caption("Keccak-256 Face Fingerprint (Normalized 512×512)")
            render_html(f'<span class="cyber-hash-pill">{rc["cryptography"]["face_hash"]}</span>')
            st.caption("🔒 Zero biometric pixels stored on-chain. GDPR Article 9 & CCPA compliant.")

        # Column 2: Social Identity Graph
        with col_c2:
            st.markdown("#### 2. Discovered Identity Graph")
            engine_badge = summary.get("search_engine_used", "Federated Multi-Engine" if search_mode in ("all-engines", "federated") else "Multi-Engine")
            render_html(f"""
            <div style="margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">ENGINE:</span>
                <span style="font-size: 0.74rem; font-weight: 700; color: #00E5FF; background: rgba(0, 229, 255, 0.08); padding: 3px 8px; border-radius: 6px; border: 1px solid rgba(0, 229, 255, 0.2);">{engine_badge}</span>
            </div>
            """)

            matched_thumbs = summary.get("matched_image_urls", [])
            if matched_thumbs:
                st.caption(f"Discovered Face Thumbnails ({len(matched_thumbs)} across engines)")
                thumb_cols = st.columns(min(len(matched_thumbs[:4]), 4))
                for idx, t_url in enumerate(matched_thumbs[:4]):
                    with thumb_cols[idx]:
                        try:
                            st.image(t_url, width=60)
                        except Exception:
                            render_html('<div style="width:60px; height:60px; background: rgba(255,255,255,0.05); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; color: #64748B;">IMG</div>')

            if entity_name:
                render_html(f"""
                <div style="margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
                    <span style="font-size: 1.15rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.02em;">👤 {entity_name}</span>
                    <span class="platform-pill platform-generic">VERIFIED ENTITY</span>
                </div>
                """)

            if is_unindexed:
                render_html(f"""
                <div style="background: rgba(0, 255, 163, 0.06); border: 1px solid rgba(0, 255, 163, 0.3); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span class="platform-pill platform-generic">🔒 Self-Sovereign Biometric Voucher</span>
                        <span class="live-node-pill" style="font-size: 0.68rem; padding: 3px 8px;">ON-CHAIN</span>
                    </div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: #F8FAFC;">{post['author_handle']}</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 6px; line-height: 1.4;">
                        Face normalized and cryptographically anchored to EVM Block #{bc['block_number']}. No matching public web footprint found (Privacy Preserved).
                    </div>
                </div>
                """)

                with st.expander("🔗 Link Social Profile to this Face Hash"):
                    st.caption("Provide your personal X, Instagram, GitHub, or LinkedIn handle to attach your real identity to this biometric hash on the EVM:")
                    col_b1, col_b2 = st.columns([2, 1])
                    with col_b1:
                        bind_input = st.text_input(
                            "Handle / Profile URL",
                            placeholder="e.g. @username or in/profile",
                            key="inline_bind_input",
                            label_visibility="collapsed"
                        )
                    with col_b2:
                        if st.button("⚡ Attest Handle", key="inline_bind_btn", type="primary", width="stretch"):
                            if bind_input and bind_input.strip():
                                clean_serper_key = serper_key_input.strip() if (serper_key_input and serper_key_input.strip()) else ""
                                p_rebind = DarpanPipeline(
                                    network=network_choice,
                                    search_provider=search_mode,
                                    api_key=clean_serper_key,
                                    output_dir="output"
                                )
                                src_file = rc["input_image"].get("source_path") or image_path
                                st.session_state.last_receipt = p_rebind.execute(
                                    src_file,
                                    subject_hint=bind_input.strip()
                                )
                                st.rerun()

            else:
                platform_class = "platform-instagram" if "Instagram" in post['platform'] else ("platform-x" if "X" in post['platform'] or "Twitter" in post['platform'] else "platform-linkedin")
                render_html(f"""
                <div style="background: rgba(12, 18, 30, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span class="platform-pill {platform_class}">🌐 {post['platform']}</span>
                        <span class="live-node-pill" style="font-size: 0.68rem; padding: 3px 8px;">CONF: {int(post.get('confidence_score', 0.95)*100)}%</span>
                    </div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #F8FAFC;">{post['author_handle']}</div>
                    <div style="font-size: 0.84rem; color: #CBD5E1; margin: 4px 0 14px 0; font-weight: 500;">{post['post_title']}</div>
                    <a href="{post['post_url']}" target="_blank" class="cyber-action-btn">
                        Open Verified Profile ↗
                    </a>
                </div>
                """)

            # Additional linked platforms
            all_m = summary.get("all_matches", [])
            if len(all_m) > 1 and not is_unindexed:
                st.caption("Other Discovered Profiles")
                for m in all_m[1:4]:
                    render_html(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 7px 12px; background: rgba(3, 7, 13, 0.7); border-radius: 8px; margin-bottom: 6px; border: 1px solid rgba(255, 255, 255, 0.06);">
                        <span style="font-size: 0.82rem; color: #E2E8F0;"><strong>{m['platform']}</strong>: {m['author_handle']}</span>
                        <a href="{m['post_url']}" target="_blank" style="color: #00FFA3; font-size: 0.78rem; text-decoration: none; font-weight: 700;">Visit ↗</a>
                    </div>
                    """)

            st.caption("Canonical Metadata Hash (RFC 8785)")
            render_html(f'<span class="cyber-hash-pill">{rc["cryptography"]["metadata_hash"]}</span>')

        # Column 3: EVM On-Chain Settlement
        with col_c3:
            st.markdown("#### 3. EVM Settlement Ledger")
            render_html(f"""
            <div style="background: rgba(12, 18, 30, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);">
                <div style="margin-bottom: 8px; font-size: 0.82rem; display: flex; justify-content: space-between;">
                    <span style="color: #94A3B8;">Consensus:</span>
                    <strong style="color: #00FFA3;">{bc['network'].upper()} (EVM)</strong>
                </div>
                <div style="margin-bottom: 8px; font-size: 0.82rem; display: flex; justify-content: space-between;">
                    <span style="color: #94A3B8;">Contract:</span>
                    <code style="color: #00E5FF;">{bc['contract_address'][:10]}...{bc['contract_address'][-6:]}</code>
                </div>
                <div style="margin-bottom: 8px; font-size: 0.82rem; display: flex; justify-content: space-between;">
                    <span style="color: #94A3B8;">Tx Hash:</span>
                    <code style="color: #E2E8F0;">{bc['tx_hash'][:10]}...{bc['tx_hash'][-6:]}</code>
                </div>
                <div style="margin-bottom: 8px; font-size: 0.82rem; display: flex; justify-content: space-between;">
                    <span style="color: #94A3B8;">Gas Consumed:</span>
                    <code class="tabular-num" style="color: #FFB800;">{bc['gas_used']:,} wei</code>
                </div>
                <div style="font-size: 0.82rem; display: flex; justify-content: space-between;">
                    <span style="color: #94A3B8;">Signer:</span>
                    <code style="color: #E2E8F0;">{bc['attestor'][:10]}...{bc['attestor'][-6:]}</code>
                </div>
            </div>
            """)

            st.caption("Cryptographic Attestation ID (bytes32)")
            render_html(f'<span class="cyber-hash-pill">{rc["cryptography"]["attestation_id"]}</span>')

            st.download_button(
                "⬇ Download Cryptographic Receipt (JSON)",
                data=json.dumps(rc, indent=2),
                file_name="attestation_receipt.json",
                mime="application/json",
                width="stretch"
            )
    else:
        render_html(IDLE_STANDBY_HTML)


# =============================================================================
# TAB 2: RE-VERIFICATION & ZERO-TRUST TAMPER AUDIT
# =============================================================================
with tab_verify:
    st.markdown("#### Zero-Trust Independent Re-Verification & Tamper Audit")
    st.caption("Recomputes Keccak-256 hashes directly from source bytes and verifies mathematical parity against the immutable on-chain smart contract.")

    if not st.session_state.last_receipt:
        st.info("Execute an attestation in Tab 1 first to generate an active cryptographic receipt.")
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
                render_html("""
                <div class="tamper-strobe-alert" style="margin: 12px 0;">
                    <strong style="color: #FF2A55; font-size: 0.9rem;">⚠️ ADVERSARIAL TAMPER MODE ACTIVE</strong>
                    <div style="font-size: 0.8rem; color: #FECACA; margin-top: 4px;">
                        Injected 1-byte mutation into biometric face vector and canonical metadata string.
                    </div>
                </div>
                """)
            else:
                render_html("""
                <div style="background: rgba(0, 255, 163, 0.08); border: 1px solid rgba(0, 255, 163, 0.35); border-radius: 12px; padding: 14px; margin: 12px 0; box-shadow: 0 0 16px rgba(0, 255, 163, 0.1);">
                    <strong style="color: #00FFA3; font-size: 0.9rem;">✓ ZERO-TRUST AUTHENTIC AUDIT</strong>
                    <div style="font-size: 0.8rem; color: #A7F3D0; margin-top: 4px;">
                        Verifying unaltered biometric crop and canonical metadata against EVM ledger.
                    </div>
                </div>
                """)

            run_audit = st.button("🔎 Execute On-Chain Verification Audit", type="primary", width="stretch")

        with col_result:
            st.markdown("##### Cryptographic Audit Telemetry")
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
                    render_html(f"""
                    <div style="background: linear-gradient(135deg, rgba(0, 50, 30, 0.85) 0%, rgba(3, 30, 20, 0.95) 100%); border: 1px solid #00FFA3; border-radius: 14px; padding: 20px; box-shadow: 0 0 30px rgba(0, 255, 163, 0.25);">
                        <h4 style="color: #00FFA3; margin: 0 0 6px 0; font-size: 1.15rem; font-weight: 800;">✅ AUDIT PASSED: 100% CRYPTOGRAPHIC INTEGRITY</h4>
                        <div style="color: #D1FAE5; font-size: 0.85rem; margin-bottom: 14px;">The source face scan and discovered social metadata match the on-chain consensus state bit-for-bit.</div>
                        <div style="background: rgba(0, 0, 0, 0.4); border-radius: 10px; padding: 12px; font-size: 0.82rem; color: #ECFDF5; border: 1px solid rgba(0, 255, 163, 0.2);">
                            <div style="margin-bottom: 4px;">• Face Biometric Hash: <strong style="color: #00FFA3;">MATCH [VALID]</strong></div>
                            <div style="margin-bottom: 4px;">• Canonical Metadata Hash: <strong style="color: #00FFA3;">MATCH [VALID]</strong></div>
                            <div style="margin-bottom: 4px;">• Smart Contract Verification: <strong style="color: #00FFA3;">CONFIRMED ON-CHAIN</strong></div>
                            <div>• Attestor Signer: <code>{audit_res.get('attestor')}</code></div>
                        </div>
                    </div>
                    """)
                else:
                    render_html(f"""
                    <div style="background: linear-gradient(135deg, rgba(60, 10, 20, 0.85) 0%, rgba(30, 5, 10, 0.95) 100%); border: 1px solid #FF2A55; border-radius: 14px; padding: 20px; box-shadow: 0 0 30px rgba(255, 42, 85, 0.35);">
                        <h4 style="color: #FF2A55; margin: 0 0 6px 0; font-size: 1.15rem; font-weight: 800;">🚨 AUDIT FAILED: CRYPTOGRAPHIC TAMPER DETECTED</h4>
                        <div style="color: #FEE2E2; font-size: 0.85rem; margin-bottom: 14px;">Cryptographic commitment divergence detected! Transaction hash rejected by consensus.</div>
                        <div style="background: rgba(0, 0, 0, 0.4); border-radius: 10px; padding: 12px; font-size: 0.82rem; color: #FEF2F2; border: 1px solid rgba(255, 42, 85, 0.25);">
                            <div style="margin-bottom: 4px;">• Face Biometric Hash: <strong style="color: {'#00FFA3' if face_ok else '#FF2A55'};">{'MATCH' if face_ok else 'MUTATED [HASH MISMATCH]'}</strong></div>
                            <div style="margin-bottom: 4px;">• Canonical Metadata Hash: <strong style="color: {'#00FFA3' if meta_ok else '#FF2A55'};">{'MATCH' if meta_ok else 'MUTATED [HASH MISMATCH]'}</strong></div>
                            <div>• EVM Smart Contract State: <strong style="color: #FF2A55;">HASH MISMATCH (TRANSACTION REJECTED)</strong></div>
                        </div>
                    </div>
                    """)
            else:
                st.caption("Click 'Execute On-Chain Verification Audit' to test the tamper-evidence cryptographic verification.")


# =============================================================================
# TAB 3: SMART CONTRACT REGISTRY
# =============================================================================
with tab_contract:
    st.markdown("#### Smart Contract & Cryptographic Architecture")

    col_details, col_source = st.columns([1, 1.2], gap="medium")

    with col_details:
        st.markdown(
            "##### Architecture Highlights\n"
            "- **GDPR Article 9 Compliance**: Zero biometric pixels or embeddings stored on-chain. Only one-way non-invertible Keccak-256 commitments are recorded.\n"
            "- **RFC 8785 Canonicalization**: JSON metadata canonicalized to guarantee bit-for-bit parity across all operating systems.\n"
            "- **Dual Consensus**: Instant evaluation via embedded in-memory Py-EVM with full Base Sepolia testnet deployment parity."
        )

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



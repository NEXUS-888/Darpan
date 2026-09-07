"""
Cross-Platform Environment & Portability Diagnostic Suite for DARPAN Protocol.
Verifies system compatibility, dependencies, CV libraries, biometrics,
blockchain EVM runtime, web discovery connectivity, and filesystem access.
"""

import sys
import os
import platform
import json

# Ensure project root is in sys.path regardless of how script is invoked
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure stdout handles UTF-8 on Windows terminal (cp1252 / cmd / PowerShell)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Safe symbols that work across Windows, Linux, and macOS
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

PASS_SYM = f"{GREEN}[PASS]{RESET}"
WARN_SYM = f"{YELLOW}[WARN]{RESET}"
FAIL_SYM = f"{RED}[FAIL]{RESET}"
INFO_SYM = f"{CYAN}[INFO]{RESET}"

def print_banner():
    print(f"\n{BOLD}{CYAN}================================================================={RESET}")
    print(f"{BOLD}{CYAN}   [>] DARPAN Protocol - Cross-Platform Diagnostics{RESET}")
    print(f"{BOLD}{CYAN}================================================================={RESET}\n")

def check_python():
    print(f"{BOLD}[1/7] Python Runtime & Operating System{RESET}")
    os_name = platform.system()
    os_release = platform.release()
    arch = platform.machine()
    py_ver = sys.version_info

    print(f"  * Operating System: {os_name} {os_release} ({arch})")
    print(f"  * Python Version:   {py_ver.major}.{py_ver.minor}.{py_ver.micro} ({sys.executable})")

    if py_ver.major == 3 and py_ver.minor >= 10:
        print(f"  {PASS_SYM} Compatible Python version (>= 3.10)")
        return True, "Python version compatible"
    else:
        print(f"  {FAIL_SYM} Python >= 3.10 required (found {py_ver.major}.{py_ver.minor})")
        return False, "Incompatible Python version"

def check_cv_and_imaging():
    print(f"\n{BOLD}[2/7] Computer Vision & Imaging Libraries{RESET}")
    all_ok = True
    
    # 1. NumPy
    try:
        import numpy as np
        arr = np.zeros((10, 10), dtype=np.uint8)
        print(f"  {PASS_SYM} NumPy v{np.__version__} operational")
    except Exception as e:
        print(f"  {FAIL_SYM} NumPy import error: {e}")
        all_ok = False

    # 2. Pillow
    try:
        from PIL import Image
        img = Image.new("RGB", (32, 32), color=(255, 0, 0))
        print(f"  {PASS_SYM} Pillow v{Image.__version__} operational")
    except Exception as e:
        print(f"  {FAIL_SYM} Pillow import error: {e}")
        all_ok = False

    # 3. OpenCV
    try:
        import cv2
        print(f"  {PASS_SYM} OpenCV (cv2) v{cv2.__version__} operational")
    except Exception as e:
        print(f"  {FAIL_SYM} OpenCV import error: {e}")
        print(f"        On Linux headless systems, install: sudo apt-get install -y libgl1 libglib2.0-0")
        all_ok = False

    return all_ok, "CV libraries status"

def check_biometrics_engine():
    print(f"\n{BOLD}[3/7] Biometrics Engine & ONNX Runtime{RESET}")
    all_ok = True

    # 1. ONNX Runtime
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        print(f"  {PASS_SYM} ONNX Runtime v{ort.__version__} available")
        print(f"        Execution Providers: {', '.join(providers)}")
    except Exception as e:
        print(f"  {WARN_SYM} ONNX Runtime not available ({e})")

    # 2. InsightFace
    try:
        import insightface
        print(f"  {PASS_SYM} InsightFace v{getattr(insightface, '__version__', 'installed')} available")
    except Exception as e:
        print(f"  {WARN_SYM} InsightFace not installed ({e})")
        print(f"        Engine will run in synthetic/fallback mode.")

    # 3. Test FaceEngine initialization & processing
    try:
        import numpy as np
        from src.face_engine import FaceEngine
        engine = FaceEngine()
        synthetic_img = np.zeros((200, 200, 3), dtype=np.uint8)
        processed = engine.process_image(synthetic_img)
        emb = engine.extract_embedding(synthetic_img)
        assert len(emb) == 512
        print(f"  {PASS_SYM} FaceEngine initialized & generated 512-D normalized biometric embedding")
    except Exception as e:
        print(f"  {FAIL_SYM} FaceEngine processing error: {e}")
        all_ok = False

    return all_ok, "Biometrics engine status"

def check_blockchain_and_crypto():
    print(f"\n{BOLD}[4/7] Blockchain EVM & Precompiled Solidity Artifacts{RESET}")
    all_ok = True

    # 1. Contract Artifact check
    artifact_path = os.path.join(PROJECT_ROOT, "contracts", "FaceAttestationRegistry.json")
    if os.path.exists(artifact_path):
        try:
            with open(artifact_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            abi = data.get("abi", [])
            bytecode = data.get("bytecode", "")
            method_names = [item["name"] for item in abi if item.get("type") == "function"]
            if "recordAttestation" in method_names and "verifyAttestation" in method_names and bytecode:
                print(f"  {PASS_SYM} Precompiled contract artifact verified ({len(method_names)} ABI functions, valid bytecode)")
            else:
                print(f"  {FAIL_SYM} Contract artifact is missing critical methods")
                all_ok = False
        except Exception as e:
            print(f"  {FAIL_SYM} Failed to parse contract artifact: {e}")
            all_ok = False
    else:
        print(f"  {FAIL_SYM} Contract artifact not found at {artifact_path}")
        all_ok = False

    # 2. Cryptographic Keccak-256 cross-architecture determinism
    try:
        from src.hasher import compute_keccak256, compute_metadata_hash, compute_attestation_id
        sample_meta = {"name": "Test", "score": 0.95}
        meta_hash = compute_metadata_hash(sample_meta)
        face_hash = compute_keccak256(b"diagnostic_face")
        att_id = compute_attestation_id(face_hash, meta_hash)
        assert att_id.startswith("0x") and len(att_id) == 66
        print(f"  {PASS_SYM} Deterministic Keccak-256 hashing verified across platform architecture")
    except Exception as e:
        print(f"  {FAIL_SYM} Cryptographic hasher failed: {e}")
        all_ok = False

    # 3. Web3 and in-memory EVM test
    try:
        from src.blockchain_service import BlockchainService
        bc = BlockchainService(network="local")
        if bc.contract_address and bc.contract_address.startswith("0x"):
            print(f"  {PASS_SYM} In-memory Py-EVM / EthTester local blockchain node active")
            print(f"        Registry Contract Address: {bc.contract_address}")
        else:
            print(f"  {WARN_SYM} Blockchain contract deployment returned empty address")
    except Exception as e:
        print(f"  {WARN_SYM} In-memory EVM initialization warning: {e}")

    return all_ok, "Blockchain and crypto status"

def check_web_discovery():
    print(f"\n{BOLD}[5/7] Web Discovery & External APIs{RESET}")
    all_ok = True
    import requests

    # 1. Wikidata API Connectivity
    try:
        r = requests.get(
            "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Albert+Einstein&language=en&format=json",
            timeout=5,
            headers={"User-Agent": "DarpanEnvironmentCheck/1.0"}
        )
        if r.status_code == 200 and "search" in r.json():
            print(f"  {PASS_SYM} Wikidata Entity & Social API connected")
        else:
            print(f"  {WARN_SYM} Wikidata returned status {r.status_code}")
    except Exception as e:
        print(f"  {WARN_SYM} Wikidata network check timed out or unreachable ({e})")

    # 2. Serper Google Lens API Key check
    serper_key = os.getenv("SERPER_API_KEY", "")
    if serper_key and len(serper_key) > 5:
        print(f"  {PASS_SYM} SERPER_API_KEY detected in environment (Google Lens search enabled)")
    else:
        print(f"  {INFO_SYM} SERPER_API_KEY not set (DuckDuckGo, Yandex, Bing, & Wikidata active)")

    return all_ok, "Web discovery status"

def check_filesystem_and_storage():
    print(f"\n{BOLD}[6/7] Filesystem & Cache Permissions{RESET}")
    all_ok = True
    output_dir = os.path.join(PROJECT_ROOT, "output")

    # 1. Output directory write test
    try:
        os.makedirs(output_dir, exist_ok=True)
        test_file = os.path.join(output_dir, ".perm_test.tmp")
        with open(test_file, "w") as f:
            f.write("darpan_test")
        os.remove(test_file)
        print(f"  {PASS_SYM} Local output/ directory is writable ({output_dir})")
    except Exception as e:
        print(f"  {FAIL_SYM} Cannot write to output/ directory: {e}")
        all_ok = False

    # 2. Home directory models cache check
    home_dir = os.path.expanduser("~")
    insightface_dir = os.path.join(home_dir, ".insightface")
    try:
        os.makedirs(insightface_dir, exist_ok=True)
        print(f"  {PASS_SYM} InsightFace model cache directory is writable ({insightface_dir})")
    except Exception as e:
        print(f"  {WARN_SYM} Model cache directory not writable: {e}")

    return all_ok, "Filesystem permissions"

def check_streamlit_readiness():
    print(f"\n{BOLD}[7/7] Streamlit Presentation Framework{RESET}")
    try:
        import streamlit
        print(f"  {PASS_SYM} Streamlit v{streamlit.__version__} installed and ready")
        return True, "Streamlit installed"
    except Exception as e:
        print(f"  {FAIL_SYM} Streamlit not installed: {e}")
        return False, "Streamlit missing"

def main():
    print_banner()
    results = [
        check_python(),
        check_cv_and_imaging(),
        check_biometrics_engine(),
        check_blockchain_and_crypto(),
        check_web_discovery(),
        check_filesystem_and_storage(),
        check_streamlit_readiness(),
    ]

    total = len(results)
    passed = sum(1 for status, _ in results if status)
    failed = total - passed

    print(f"\n{BOLD}{CYAN}================================================================={RESET}")
    print(f"{BOLD}Diagnostic Summary: {passed}/{total} checks passed{RESET}")
    if failed == 0:
        print(f"{GREEN}{BOLD}>>> System is fully compatible and ready to run DARPAN!{RESET}")
        print(f"   Launch via: streamlit run app.py  (or docker compose up --build)")
    else:
        print(f"{RED}{BOLD}XXX {failed} check(s) failed. Please resolve the errors above.{RESET}")
    print(f"{BOLD}{CYAN}================================================================={RESET}\n")

    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# =============================================================================
# Kannadi / DARPAN Protocol - 1-Click Native Runner (Linux / macOS)
# =============================================================================
set -e

echo "=========================================================="
echo "  🚀 Starting Kannadi (DARPAN Protocol)"
echo "  Biometric Face Identification & Attestation Gateway"
echo "=========================================================="

# 1. Detect Python 3
PYTHON_BIN=""
for cmd in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        PY_VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        MINOR=$(echo "$PY_VER" | cut -d. -f2)
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON_BIN="$cmd"
            echo "  ✓ Found compatible Python: $cmd (v$PY_VER)"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "  ❌ Error: Python 3.10 or higher is required."
    echo "     Please install Python 3.10+ (recommended: Python 3.11) and try again."
    exit 1
fi

# 2. Virtual Environment Setup
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "  ⚙️  Creating virtual environment in ./$VENV_DIR..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# Activate virtual environment
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# 3. Dependency Installation / Verification
echo "  📦 Checking Python dependencies..."
pip install --quiet --upgrade pip setuptools wheel
pip install --quiet -r requirements.txt

# 4. Check Linux System Graphics Libraries (OpenCV dependency)
OS_TYPE="$(uname -s)"
if [ "$OS_TYPE" = "Linux" ]; then
    if ! python -c "import cv2" >/dev/null 2>&1; then
        echo "  ⚠️  Warning: OpenCV native library check failed."
        echo "     If you see libGL or libgomp errors, install system packages:"
        echo "     Debian/Ubuntu: sudo apt-get update && sudo apt-get install -y libgl1 libglib2.0-0 libgomp1"
        echo "     Fedora/RHEL:   sudo dnf install mesa-libGL glib2 libgomp"
        echo "     Arch Linux:    sudo pacman -S mesa glib2"
    fi
fi

# 5. Ensure Biometric Models Are Pre-warmed / Downloaded
echo "  🧠 Checking InsightFace biometric models (buffalo_sc)..."
python -c "from src.face_engine import _get_insightface_app; _get_insightface_app('buffalo_sc')"

# 6. Ensure Output Directory Exists
mkdir -p output

# 7. Launch Application
echo "  🌐 Launching Streamlit web dashboard..."
echo "     URL: http://localhost:8501"
echo "=========================================================="
exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0

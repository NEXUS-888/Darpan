@echo off
setlocal enabledelayedexpansion

title DARPAN - Biometric Face Identification & Attestation Gateway

echo ==========================================================
echo   🚀 Starting DARPAN Protocol
echo   Biometric Face Identification ^& Attestation Gateway
echo ==========================================================

:: 1. Check Python Availability
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    where py >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo   ❌ Error: Python is not found in your PATH.
        echo      Please install Python 3.10+ from python.org and ensure
        echo      "Add Python to PATH" is checked during installation.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py -3
    )
) else (
    set PYTHON_CMD=python
)

echo   ✓ Python found: %PYTHON_CMD%

:: 2. Setup Virtual Environment
if not exist "venv\Scripts\activate.bat" (
    echo   ⚙️  Creating virtual environment in .\venv...
    %PYTHON_CMD% -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo   ❌ Error: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: 3. Install/Update Dependencies
echo   📦 Checking Python dependencies...
python -m pip install --quiet --upgrade pip setuptools wheel
python -m pip install --quiet -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo   ⚠️  Warning: Pip dependency installation encountered warnings or errors.
    echo      Attempting to continue...
)

:: 4. Ensure Biometric Models Are Pre-warmed / Downloaded
echo   🧠 Checking InsightFace biometric models (buffalo_sc)...
python -c "from src.face_engine import _get_insightface_app; _get_insightface_app('buffalo_sc')"

:: 5. Ensure Output Directory Exists
if not exist "output" mkdir output

:: 6. Launch Application
echo   🌐 Launching Streamlit web dashboard...
echo      URL: http://localhost:8501
echo ==========================================================
streamlit run app.py --server.port=8501 --server.address=localhost

pause

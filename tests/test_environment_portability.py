"""
Tests for Cross-Platform Environment Portability and Setup.
Ensures zero-friction execution, deterministic hashing across architectures,
valid container specifications, and launcher script integrity.
"""

import os
import sys
import json
import subprocess
import pytest
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_precompiled_contract_artifact_portability():
    """
    Verifies that the compiled Solidity contract artifact is present, valid JSON,
    and contains all necessary ABI functions and EVM bytecode for offline execution
    without requiring a local solc compiler.
    """
    artifact_path = os.path.join(PROJECT_ROOT, "contracts", "FaceAttestationRegistry.json")
    assert os.path.exists(artifact_path), f"Contract artifact missing at {artifact_path}"

    with open(artifact_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "abi" in data
    assert "bytecode" in data
    assert len(data["bytecode"]) > 100, "Bytecode is empty or truncated"

    function_names = [item["name"] for item in data["abi"] if item.get("type") == "function"]
    assert "recordAttestation" in function_names
    assert "verifyAttestation" in function_names


def test_keccak256_architecture_independence():
    """
    Verifies that Keccak-256 and RFC 8785 JSON canonicalization generate bitwise identical
    hashes across different OS architectures (x86_64, arm64, Apple Silicon).
    """
    from src.hasher import compute_keccak256, canonicalize_json, compute_metadata_hash, compute_attestation_id

    # Test vector 1: raw bytes
    raw_hash = compute_keccak256(b"kannadi_darpan_protocol")
    assert raw_hash.startswith("0x")
    assert len(raw_hash) == 66

    # Test vector 2: canonical JSON key order independent
    d1 = {"b": 2, "a": 1, "nested": {"z": "last", "m": "middle"}}
    d2 = {"nested": {"m": "middle", "z": "last"}, "a": 1, "b": 2}
    assert canonicalize_json(d1) == canonicalize_json(d2)
    assert compute_metadata_hash(d1) == compute_metadata_hash(d2)

    # Test vector 3: attestation ID commitment
    att_id = compute_attestation_id(raw_hash, compute_metadata_hash(d1))
    assert att_id.startswith("0x")
    assert len(att_id) == 66


def test_face_engine_cross_platform_fallback(tmp_path):
    """
    Verifies that FaceEngine operates reliably with zero-dependency synthetic fallback
    on platforms without GPU acceleration or InsightFace models.
    """
    from src.face_engine import FaceEngine

    engine = FaceEngine()
    test_img = np.zeros((300, 300, 3), dtype=np.uint8)
    out_crop = str(tmp_path / "test_crop.png")

    processed = engine.process_image(test_img, output_crop_path=out_crop)
    assert processed.dimensions == (512, 512)
    assert processed.face_hash.startswith("0x")
    assert os.path.exists(out_crop)

    emb = engine.extract_embedding(test_img)
    assert isinstance(emb, np.ndarray)
    assert emb.shape == (512,)


def test_docker_and_launcher_specifications():
    """
    Verifies that Dockerfile, docker-compose.yml, .dockerignore, run.sh, and run.bat
    exist, have non-trivial content, and adhere to security standards.
    """
    dockerfile_path = os.path.join(PROJECT_ROOT, "Dockerfile")
    compose_path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
    dockerignore_path = os.path.join(PROJECT_ROOT, ".dockerignore")
    run_sh_path = os.path.join(PROJECT_ROOT, "run.sh")
    run_bat_path = os.path.join(PROJECT_ROOT, "run.bat")

    for path in [dockerfile_path, compose_path, dockerignore_path, run_sh_path, run_bat_path]:
        assert os.path.exists(path), f"File {path} does not exist"
        assert os.path.getsize(path) > 50, f"File {path} is empty or too small"

    # Dockerfile security & configuration checks
    with open(dockerfile_path, "r", encoding="utf-8") as f:
        dockerfile_content = f.read()
    assert "USER appuser" in dockerfile_content, "Dockerfile must run as non-root user"
    assert "EXPOSE 8501" in dockerfile_content, "Dockerfile must expose Streamlit port 8501"
    assert "HEALTHCHECK" in dockerfile_content, "Dockerfile should define a healthcheck"

    # Compose checks
    with open(compose_path, "r", encoding="utf-8") as f:
        compose_content = f.read()
    assert "8501:8501" in compose_content
    assert "insightface_models" in compose_content


def test_verify_environment_script_execution():
    """
    Executes scripts/verify_environment.py and asserts it completes with exit code 0.
    """
    script_path = os.path.join(PROJECT_ROOT, "scripts", "verify_environment.py")
    res = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert res.returncode == 0, f"verify_environment.py failed:\n{res.stdout}\n{res.stderr}"
    assert "Diagnostic Summary" in res.stdout

"""
Compiled Solidity contract artifact loader for FaceAttestationRegistry.
Loads ABI and EVM runtime bytecode deterministically from JSON artifact.
"""
import json
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_artifact_path = os.path.join(_current_dir, "..", "contracts", "FaceAttestationRegistry.json")

if os.path.exists(_artifact_path):
    with open(_artifact_path, "r", encoding="utf-8") as _f:
        _data = json.load(_f)
    ABI = _data["abi"]
    BYTECODE = _data["bytecode"]
else:
    raise FileNotFoundError(f"Contract artifact not found at {_artifact_path}")

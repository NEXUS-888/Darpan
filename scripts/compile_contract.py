"""
Compile FaceAttestationRegistry.sol and export ABI and bytecode artifacts.
"""
import os
import json
import solcx

def compile_contract():
    solc_version = "0.8.20"
    print(f"Ensuring solc {solc_version} is installed...")
    try:
        solcx.install_solc(solc_version)
    except Exception as e:
        print(f"Notice during install_solc: {e}")

    contract_path = os.path.join(os.path.dirname(__file__), "..", "contracts", "FaceAttestationRegistry.sol")
    contract_path = os.path.abspath(contract_path)

    with open(contract_path, "r", encoding="utf-8") as f:
        source = f.read()

    print("Compiling contract...")
    compiled = solcx.compile_standard({
        "language": "Solidity",
        "sources": {"FaceAttestationRegistry.sol": {"content": source}},
        "settings": {
            "optimizer": {"enabled": True, "runs": 200},
            "outputSelection": {
                "*": {"*": ["abi", "evm.bytecode"]}
            }
        }
    }, solc_version=solc_version)

    contract_data = compiled["contracts"]["FaceAttestationRegistry.sol"]["FaceAttestationRegistry"]
    abi = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]

    # Save to contracts/FaceAttestationRegistry.json
    out_json = os.path.join(os.path.dirname(__file__), "..", "contracts", "FaceAttestationRegistry.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"contractName": "FaceAttestationRegistry", "abi": abi, "bytecode": bytecode}, f, indent=2)

    # Save to src/contract_artifact.py
    src_dir = os.path.join(os.path.dirname(__file__), "..", "src")
    os.makedirs(src_dir, exist_ok=True)
    out_py = os.path.join(src_dir, "contract_artifact.py")
    with open(out_py, "w", encoding="utf-8") as f:
        f.write('"""Auto-generated compiled Solidity contract artifact for FaceAttestationRegistry."""\n\n')
        f.write(f'ABI = {json.dumps(abi, indent=2)}\n\n')
        f.write(f'BYTECODE = "{bytecode}"\n')

    print(f"Compilation successful!")
    print(f"Exported JSON: {out_json}")
    print(f"Exported Python artifact: {out_py}")
    print(f"ABI functions count: {len(abi)}, Bytecode length: {len(bytecode)}")

if __name__ == "__main__":
    compile_contract()

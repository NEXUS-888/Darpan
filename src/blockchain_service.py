"""
Blockchain Service for the VeriFace Protocol.
Provides dual-engine execution:
- Local EVM: Instant, zero-cost, zero-setup embedded Ethereum Virtual Machine (py-evm / eth-tester).
- Remote Testnet: Base Sepolia, Polygon Amoy, or any standard EVM RPC endpoint.
"""
import os
import time
from typing import Dict, Any, Optional, Tuple
from web3 import Web3, EthereumTesterProvider
from eth_tester import EthereumTester, PyEVMBackend
from hexbytes import HexBytes

from .contract_artifact import ABI, BYTECODE


class BlockchainService:
    def __init__(
        self,
        network: str = "local",
        rpc_url: Optional[str] = None,
        private_key: Optional[str] = None,
        contract_address: Optional[str] = None,
    ):
        self.network = network.lower()
        self.contract_address = contract_address
        self.private_key = private_key or os.getenv("WALLET_PRIVATE_KEY")
        
        # Initialize Web3 Provider
        if self.network == "local":
            self.tester = EthereumTester(PyEVMBackend())
            self.provider = EthereumTesterProvider(self.tester)
            self.w3 = Web3(self.provider)
            self.account = self.w3.eth.accounts[0]
        else:
            rpc = rpc_url or self._get_default_rpc(self.network)
            self.w3 = Web3(Web3.HTTPProvider(rpc))
            if not self.w3.is_connected():
                raise ConnectionError(f"Could not connect to EVM RPC at {rpc}")
            if not self.private_key:
                raise ValueError("WALLET_PRIVATE_KEY is required for remote testnet broadcasting")
            self.account = self.w3.eth.account.from_key(self.private_key).address

        self.contract = None
        if self.contract_address:
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=ABI
            )
        else:
            # Automatically deploy contract if no address is specified
            self.deploy_contract()

    def _get_default_rpc(self, network: str) -> str:
        rpc_map = {
            "base-sepolia": os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org"),
            "polygon-amoy": os.getenv("POLYGON_AMOY_RPC", "https://rpc-amoy.polygon.technology"),
            "sepolia": os.getenv("SEPOLIA_RPC", "https://rpc.sepolia.org"),
        }
        return rpc_map.get(network, "https://sepolia.base.org")

    def deploy_contract(self) -> str:
        """
        Deploys FaceAttestationRegistry contract to the current network.
        """
        ContractFactory = self.w3.eth.contract(abi=ABI, bytecode=BYTECODE)
        
        if self.network == "local":
            tx_hash = ContractFactory.constructor().transact({"from": self.account})
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.contract_address = receipt.contractAddress
        else:
            nonce = self.w3.eth.get_transaction_count(self.account)
            construct_tx = ContractFactory.constructor().build_transaction({
                "from": self.account,
                "nonce": nonce,
                "gas": 3000000,
                "gasPrice": self.w3.eth.gas_price,
            })
            signed_tx = self.w3.eth.account.sign_transaction(construct_tx, private_key=self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.contract_address = receipt.contractAddress

        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=ABI
        )
        return self.contract_address

    def record_attestation(
        self,
        attestation_id: str,
        face_hash: str,
        metadata_hash: str,
        post_url: str
    ) -> Dict[str, Any]:
        """
        Submits attestation commitment to the blockchain.
        """
        if not self.contract:
            raise RuntimeError("Smart contract not initialized")

        id_bytes32 = HexBytes(attestation_id)
        f_bytes32 = HexBytes(face_hash)
        m_bytes32 = HexBytes(metadata_hash)

        if self.network == "local":
            tx_hash = self.contract.functions.recordAttestation(
                id_bytes32,
                f_bytes32,
                m_bytes32,
                post_url
            ).transact({"from": self.account})
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        else:
            nonce = self.w3.eth.get_transaction_count(self.account)
            tx = self.contract.functions.recordAttestation(
                id_bytes32,
                f_bytes32,
                m_bytes32,
                post_url
            ).build_transaction({
                "from": self.account,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": self.w3.eth.gas_price,
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        block = self.w3.eth.get_block(receipt.blockNumber)
        
        return {
            "network": self.network,
            "contract_address": self.contract_address,
            "tx_hash": "0x" + receipt.transactionHash.hex().removeprefix("0x"),
            "block_number": receipt.blockNumber,
            "block_timestamp": block.timestamp,
            "gas_used": receipt.gasUsed,
            "attestor": self.account,
            "status": "SUCCESS" if receipt.status == 1 else "FAILED",
        }

    def verify_attestation(
        self,
        attestation_id: str,
        face_hash: str,
        metadata_hash: str
    ) -> Dict[str, Any]:
        """
        Queries smart contract view function to verify attestation validity against on-chain state.
        """
        if not self.contract:
            raise RuntimeError("Smart contract not initialized")

        id_bytes32 = HexBytes(attestation_id)
        f_bytes32 = HexBytes(face_hash)
        m_bytes32 = HexBytes(metadata_hash)

        exists = self.contract.functions.attestationExists(id_bytes32).call()
        if not exists:
            return {
                "exists": False,
                "is_valid": False,
                "recorded_timestamp": 0,
                "attestor": "0x0000000000000000000000000000000000000000",
                "message": "Attestation record not found on-chain",
            }

        is_valid, timestamp, attestor = self.contract.functions.verifyAttestation(
            id_bytes32,
            f_bytes32,
            m_bytes32
        ).call()

        return {
            "exists": True,
            "is_valid": is_valid,
            "recorded_timestamp": timestamp,
            "attestor": attestor,
            "message": "Cryptographic proof matches on-chain commitment" if is_valid else "Hash mismatch: data tampered",
        }

    def get_attestation(self, attestation_id: str) -> Dict[str, Any]:
        """
        Retrieves the raw on-chain struct for a given attestationId.
        """
        id_bytes32 = HexBytes(attestation_id)
        record = self.contract.functions.getAttestation(id_bytes32).call()
        return {
            "face_hash": "0x" + record[0].hex(),
            "metadata_hash": "0x" + record[1].hex(),
            "post_url": record[2],
            "attestor": record[3],
            "timestamp": record[4],
            "block_number": record[5],
            "exists": record[6],
        }

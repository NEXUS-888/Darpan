// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title FaceAttestationRegistry
 * @dev Tamper-evident registry for facial identification and social post attestations.
 * Stores 32-byte cryptographic commitments (hashes) rather than raw biometrics or PII.
 */
contract FaceAttestationRegistry {
    struct Attestation {
        bytes32 faceHash;         // Keccak-256 hash of the normalized face crop
        bytes32 metadataHash;     // Keccak-256 hash of canonical post metadata
        string postUrl;           // URL of the discovered social media post
        address attestor;         // Account address that submitted the attestation
        uint64 timestamp;         // Block timestamp when recorded
        uint64 blockNumber;       // Block number of the transaction
        bool exists;              // True if record exists
    }

    // Mapping from unique attestationId -> Attestation record
    mapping(bytes32 => Attestation) private _attestations;

    // Mapping from faceHash -> array of attestation IDs
    mapping(bytes32 => bytes32[]) private _faceToAttestations;

    // Total number of recorded attestations
    uint256 public totalAttestations;

    event AttestationRecorded(
        bytes32 indexed attestationId,
        bytes32 indexed faceHash,
        bytes32 metadataHash,
        string postUrl,
        address indexed attestor,
        uint256 timestamp,
        uint256 blockNumber
    );

    error AttestationAlreadyExists(bytes32 attestationId);
    error AttestationNotFound(bytes32 attestationId);
    error InvalidParameter(string message);

    /**
     * @notice Records a new face-to-social post attestation on-chain.
     * @param attestationId Expected commitment: keccak256(abi.encodePacked(faceHash, metadataHash))
     * @param faceHash Keccak-256 hash of the normalized face scan/crop
     * @param metadataHash Keccak-256 hash of the canonical social post metadata
     * @param postUrl URL of the discovered social media post
     * @return id The confirmed attestationId
     */
    function recordAttestation(
        bytes32 attestationId,
        bytes32 faceHash,
        bytes32 metadataHash,
        string calldata postUrl
    ) external returns (bytes32 id) {
        if (faceHash == bytes32(0)) {
            revert InvalidParameter("Face hash cannot be zero");
        }
        if (metadataHash == bytes32(0)) {
            revert InvalidParameter("Metadata hash cannot be zero");
        }
        if (bytes(postUrl).length == 0) {
            revert InvalidParameter("Post URL cannot be empty");
        }
        if (_attestations[attestationId].exists) {
            revert AttestationAlreadyExists(attestationId);
        }

        // Cryptographic validation of commitment
        bytes32 computedId = keccak256(abi.encodePacked(faceHash, metadataHash));
        if (computedId != attestationId) {
            revert InvalidParameter("Commitment mismatch: attestationId != keccak256(faceHash, metadataHash)");
        }

        _attestations[attestationId] = Attestation({
            faceHash: faceHash,
            metadataHash: metadataHash,
            postUrl: postUrl,
            attestor: msg.sender,
            timestamp: uint64(block.timestamp),
            blockNumber: uint64(block.number),
            exists: true
        });

        _faceToAttestations[faceHash].push(attestationId);
        totalAttestations++;

        emit AttestationRecorded(
            attestationId,
            faceHash,
            metadataHash,
            postUrl,
            msg.sender,
            block.timestamp,
            block.number
        );

        return attestationId;
    }

    /**
     * @notice Verifies whether a given faceHash and metadataHash match an on-chain record.
     * @param attestationId The attestation identifier to check
     * @param faceHash The face hash to verify
     * @param metadataHash The metadata hash to verify
     * @return isValid True if the record exists and hashes match perfectly
     * @return recordedTimestamp Block timestamp of original attestation
     * @return attestor Address of the attestor
     */
    function verifyAttestation(
        bytes32 attestationId,
        bytes32 faceHash,
        bytes32 metadataHash
    ) external view returns (bool isValid, uint64 recordedTimestamp, address attestor) {
        Attestation memory record = _attestations[attestationId];
        if (!record.exists) {
            return (false, 0, address(0));
        }

        bool matchValid = (record.faceHash == faceHash && record.metadataHash == metadataHash);
        return (matchValid, record.timestamp, record.attestor);
    }

    /**
     * @notice Retrieves the complete attestation record by attestationId.
     */
    function getAttestation(bytes32 attestationId) external view returns (Attestation memory) {
        if (!_attestations[attestationId].exists) {
            revert AttestationNotFound(attestationId);
        }
        return _attestations[attestationId];
    }

    /**
     * @notice Checks whether an attestation exists.
     */
    function attestationExists(bytes32 attestationId) external view returns (bool) {
        return _attestations[attestationId].exists;
    }

    /**
     * @notice Returns all attestation IDs associated with a given face hash.
     */
    function getAttestationsByFace(bytes32 faceHash) external view returns (bytes32[] memory) {
        return _faceToAttestations[faceHash];
    }
}

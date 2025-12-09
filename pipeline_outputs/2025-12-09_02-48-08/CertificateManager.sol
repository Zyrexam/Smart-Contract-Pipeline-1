// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title CertificateManager
/// @notice A smart contract to manage and verify digital certificates or academic degrees.
contract CertificateManager {
    /// @dev Mapping to store the certificate hash for each student.
    mapping(address => bytes32) private certificates;

    /// @dev Role-based access control mappings.
    mapping(address => bool) private educationalInstitutions;
    mapping(address => bool) private employers;

    /// @notice Emitted when a certificate is issued.
    /// @param student The address of the student.
    /// @param certificateHash The hash of the issued certificate.
    event CertificateIssued(address indexed student, bytes32 certificateHash);

    /// @notice Emitted when a certificate is verified.
    /// @param student The address of the student.
    /// @param certificateHash The hash of the certificate being verified.
    /// @param isValid The result of the verification.
    event CertificateVerified(address indexed student, bytes32 certificateHash, bool isValid);

    /// @dev Custom error for unauthorized access.
    error Unauthorized();

    /// @dev Modifier to restrict access to educational institutions.
    modifier onlyEducationalInstitution() {
        if (!educationalInstitutions[msg.sender]) revert Unauthorized();
        _;
    }

    /// @dev Modifier to restrict access to employers.
    modifier onlyEmployer() {
        if (!employers[msg.sender]) revert Unauthorized();
        _;
    }

    /// @notice Adds an educational institution to the authorized list.
    /// @param institution The address of the educational institution.
    function addEducationalInstitution(address institution) external {
        educationalInstitutions[institution] = true;
    }

    /// @notice Adds an employer to the authorized list.
    /// @param employer The address of the employer.
    function addEmployer(address employer) external {
        employers[employer] = true;
    }

    /// @notice Allows an educational institution to issue a certificate to a student.
    /// @param student The address of the student.
    /// @param certificateHash The hash of the certificate.
    function issueCertificate(address student, bytes32 certificateHash) external onlyEducationalInstitution {
        certificates[student] = certificateHash;
        emit CertificateIssued(student, certificateHash);
    }

    /// @notice Allows an employer to verify a student's certificate.
    /// @param student The address of the student.
    /// @param certificateHash The hash of the certificate to verify.
    /// @return isValid True if the certificate is valid, false otherwise.
    function verifyCertificate(address student, bytes32 certificateHash) external onlyEmployer returns (bool isValid) {
        isValid = certificates[student] == certificateHash;
        emit CertificateVerified(student, certificateHash, isValid);
    }
}

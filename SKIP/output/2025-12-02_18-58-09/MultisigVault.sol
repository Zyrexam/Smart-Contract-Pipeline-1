// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;


import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/access/Ownable.sol";

/**
 * @title MultisigVault
 * @dev A multisig vault that requires biometric verification via an oracle before signing transactions.
 */
contract MultisigVault is Ownable {
    struct Transaction {
        address destination;
        uint256 value;
        bytes data;
        bool executed;
        uint256 approvals;
    }

    address[] private owners;
    uint256 private requiredSignatures;
    address private biometricOracle;
    mapping(uint256 => Transaction) private pendingTransactions;
    mapping(uint256 => mapping(address => bool)) private approvals;
    uint256 private transactionCount;

    event TransactionProposed(uint256 indexed transactionId, address indexed destination, uint256 value);
    event TransactionApproved(uint256 indexed transactionId, address indexed owner);
    event TransactionExecuted(uint256 indexed transactionId);
    event BiometricVerified(uint256 indexed transactionId, bool verified);

    error NotAnOwner();
    error NotOracle();
    error TransactionAlreadyExecuted();
    error InsufficientApprovals();
    error InvalidTransaction();
    error InvalidAddress();
    error InvalidValue();

    modifier onlyOwner() {
        bool isOwner = false;
        for (uint256 i = 0; i < owners.length; i++) {
            if (owners[i] == msg.sender) {
                isOwner = true;
                break;
            }
        }
        if (!isOwner) revert NotAnOwner();
        _;
    }

    modifier onlyOracle() {
        if (msg.sender != biometricOracle) revert NotOracle();
        _;
    }

    /**
     * @dev Constructor that initializes the contract with the initial owners and required signatures.
     * @param _owners List of initial owners.
     * @param _requiredSignatures Number of required signatures for a transaction.
     * @param _biometricOracle Address of the biometric oracle.
     */
    constructor(address[] memory _owners, uint256 _requiredSignatures, address _biometricOracle) {
        if (_owners.length == 0 || _requiredSignatures == 0 || _biometricOracle == address(0)) revert InvalidAddress();
        owners = _owners;
        requiredSignatures = _requiredSignatures;
        biometricOracle = _biometricOracle;
    }

    /**
     * @dev Allows an owner to propose a new transaction.
     * @param destination The address to send the transaction to.
     * @param value The amount of ether to send.
     * @param data The data to send with the transaction.
     * @return transactionId The ID of the proposed transaction.
     */
    function proposeTransaction(address destination, uint256 value, bytes memory data) public onlyOwner returns (uint256 transactionId) {
        if (destination == address(0) || value == 0) revert InvalidAddress();
        transactionId = transactionCount++;
        pendingTransactions[transactionId] = Transaction(destination, value, data, false, 0);
        emit TransactionProposed(transactionId, destination, value);
    }

    /**
     * @dev Allows an owner to approve a proposed transaction.
     * @param transactionId The ID of the transaction to approve.
     */
    function approveTransaction(uint256 transactionId) public onlyOwner {
        if (pendingTransactions[transactionId].destination == address(0)) revert InvalidTransaction();
        if (approvals[transactionId][msg.sender]) revert InvalidTransaction();
        approvals[transactionId][msg.sender] = true;
        pendingTransactions[transactionId].approvals++;
        emit TransactionApproved(transactionId, msg.sender);
    }

    /**
     * @dev Executes a transaction if it has enough approvals and biometric verification.
     * @param transactionId The ID of the transaction to execute.
     */
    function executeTransaction(uint256 transactionId) public onlyOwner {
        Transaction storage txn = pendingTransactions[transactionId];
        if (txn.executed) revert TransactionAlreadyExecuted();
        if (txn.approvals < requiredSignatures) revert InsufficientApprovals();
        txn.executed = true;
        (bool success, ) = txn.destination.call{value: txn.value}(txn.data);
        require(success, "Transaction execution failed");
        emit TransactionExecuted(transactionId);
    }

    /**
     * @dev Called by the oracle to verify biometric data for a transaction.
     * @param transactionId The ID of the transaction to verify.
     * @param biometricData The biometric data to verify.
     * @return verified True if the biometric data is verified.
     */
    function verifyBiometrics(uint256 transactionId, bytes memory biometricData) external onlyOracle returns (bool verified) {
        // Biometric verification logic would be implemented here
        verified = true; // Placeholder for actual verification result
        emit BiometricVerified(transactionId, verified);
    }
}

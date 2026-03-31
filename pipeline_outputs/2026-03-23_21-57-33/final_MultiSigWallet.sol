// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract MultiSigWallet is AccessControl {
    using SafeERC20 for IERC20;

    struct Transaction {
        address destination;
        uint value;
        bytes data;
        bool executed;
        uint approvalCount;
    }

    bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");

    address[] private owners;
    uint private requiredApprovals;
    Transaction[] private transactions;
    mapping(uint => mapping(address => bool)) private approvals;

    event TransactionSubmitted(uint indexed transactionId);
    event TransactionApproved(uint indexed transactionId, address indexed owner);
    event TransactionExecuted(uint indexed transactionId);
    event ApprovalRevoked(uint indexed transactionId, address indexed owner);

    error NotOwner();
    error TransactionAlreadyExecuted();
    error TransactionNotApproved();
    error InsufficientApprovals();

    constructor(address[] memory initialOwners, uint initialRequiredApprovals) {
        require(initialOwners.length > 0, "Owners required");
        require(initialRequiredApprovals > 0 && initialRequiredApprovals <= initialOwners.length, "Invalid number of required approvals");

        for (uint i = 0; i < initialOwners.length; i++) {
            _grantRole(OWNER_ROLE, initialOwners[i]);
            owners.push(initialOwners[i]);
        }
        requiredApprovals = initialRequiredApprovals;
    }

    modifier onlyOwner() {
        if (!hasRole(OWNER_ROLE, msg.sender)) revert NotOwner();
        _;
    }

    function submitTransaction(address destination, uint value, bytes memory data) public onlyOwner returns (uint transactionId) {
        transactionId = transactions.length;
        transactions.push(Transaction({
            destination: destination,
            value: value,
            data: data,
            executed: false,
            approvalCount: 0
        }));
        emit TransactionSubmitted(transactionId);
    }

    function approveTransaction(uint transactionId) public onlyOwner {
        Transaction storage txn = transactions[transactionId];
        if (txn.executed) revert TransactionAlreadyExecuted();
        if (approvals[transactionId][msg.sender]) revert TransactionNotApproved();

        approvals[transactionId][msg.sender] = true;
        txn.approvalCount += 1;
        emit TransactionApproved(transactionId, msg.sender);
    }

    function revokeApproval(uint transactionId) public onlyOwner {
        Transaction storage txn = transactions[transactionId];
        if (txn.executed) revert TransactionAlreadyExecuted();
        if (!approvals[transactionId][msg.sender]) revert TransactionNotApproved();

        approvals[transactionId][msg.sender] = false;
        txn.approvalCount -= 1;
        emit ApprovalRevoked(transactionId, msg.sender);
    }

    function executeTransaction(uint transactionId) public onlyOwner {
        Transaction storage txn = transactions[transactionId];
        if (txn.executed) revert TransactionAlreadyExecuted();
        if (txn.approvalCount < requiredApprovals) revert InsufficientApprovals();

        txn.executed = true;
        (bool success, ) = txn.destination.call{value: txn.value}(txn.data);
        require(success, "Transaction failed");
        emit TransactionExecuted(transactionId);
    }

    function getTransactionDetails(uint transactionId) public view returns (address destination, uint value, bytes memory data, bool executed) {
        Transaction storage txn = transactions[transactionId];
        return (txn.destination, txn.value, txn.data, txn.executed);
    }
}
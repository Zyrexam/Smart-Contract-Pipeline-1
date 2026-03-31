// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract MultiSigWallet is AccessControl {
    using SafeERC20 for IERC20;

    bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");

    struct Transaction {
        address destination;
        uint256 value;
        bytes data;
        bool executed;
        uint256 approvalCount;
    }

    address[] private owners;
    uint256 private requiredApprovals;
    mapping(uint256 => Transaction) private transactions;
    mapping(uint256 => mapping(address => bool)) private approvals;
    uint256 private transactionCount;

    event TransactionSubmitted(uint256 indexed transactionId, address indexed destination, uint256 value);
    event TransactionApproved(uint256 indexed transactionId, address indexed owner);
    event TransactionExecuted(uint256 indexed transactionId);

    error NotOwner();
    error TransactionDoesNotExist();
    error TransactionAlreadyExecuted();
    error TransactionAlreadyApproved();
    error InsufficientApprovals();

    constructor(address[] memory initialOwners, uint256 initialRequiredApprovals) {
        require(initialOwners.length > 0, "Owners required");
        require(initialRequiredApprovals > 0 && initialRequiredApprovals <= initialOwners.length, "Invalid number of required approvals");

        for (uint256 i = 0; i < initialOwners.length; i++) {
            _grantRole(OWNER_ROLE, initialOwners[i]);
            owners.push(initialOwners[i]);
        }
        requiredApprovals = initialRequiredApprovals;
    }

    modifier onlyOwner() {
        if (!hasRole(OWNER_ROLE, msg.sender)) revert NotOwner();
        _;
    }

    modifier transactionExists(uint256 transactionId) {
        if (transactions[transactionId].destination == address(0)) revert TransactionDoesNotExist();
        _;
    }

    modifier notExecuted(uint256 transactionId) {
        if (transactions[transactionId].executed) revert TransactionAlreadyExecuted();
        _;
    }

    modifier notApproved(uint256 transactionId) {
        if (approvals[transactionId][msg.sender]) revert TransactionAlreadyApproved();
        _;
    }

    function submitTransaction(address destination, uint256 value, bytes memory data)
        public
        onlyOwner
        returns (uint256 transactionId)
    {
        transactionId = transactionCount++;
        transactions[transactionId] = Transaction({
            destination: destination,
            value: value,
            data: data,
            executed: false,
            approvalCount: 0
        });
        emit TransactionSubmitted(transactionId, destination, value);
    }

    function approveTransaction(uint256 transactionId)
        public
        onlyOwner
        transactionExists(transactionId)
        notExecuted(transactionId)
        notApproved(transactionId)
    {
        approvals[transactionId][msg.sender] = true;
        transactions[transactionId].approvalCount += 1;
        emit TransactionApproved(transactionId, msg.sender);
    }

    function executeTransaction(uint256 transactionId)
        public
        onlyOwner
        transactionExists(transactionId)
        notExecuted(transactionId)
    {
        Transaction storage txn = transactions[transactionId];
        if (txn.approvalCount < requiredApprovals) revert InsufficientApprovals();

        txn.executed = true;
        (bool success, ) = txn.destination.call{value: txn.value}(txn.data);
        require(success, "Transaction failed");

        emit TransactionExecuted(transactionId);
    }

    receive() external payable {}
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Escrow Contract
/// @notice An escrow smart contract that holds funds until both parties approve the transaction.
contract Escrow {
    address public partyA;
    address public partyB;
    uint256 private funds;
    bool private partyAApproved;
    bool private partyBApproved;

    /// @notice Emitted when funds are deposited into the escrow.
    /// @param amount The amount of funds deposited.
    event FundsDeposited(uint256 amount);

    /// @notice Emitted when a party approves the transaction.
    /// @param party The address of the party that approved the transaction.
    event TransactionApproved(address indexed party);

    /// @notice Emitted when funds are released to the recipient.
    /// @param recipient The address of the recipient.
    event FundsReleased(address indexed recipient);

    /// @notice Emitted when funds are refunded to the depositor.
    /// @param depositor The address of the depositor.
    event FundsRefunded(address indexed depositor);

    /// @dev Custom error for unauthorized access.
    error Unauthorized();

    /// @dev Custom error for insufficient funds.
    error InsufficientFunds();

    /// @dev Custom error for already approved transactions.
    error AlreadyApproved();

    /// @dev Custom error for incomplete approvals.
    error IncompleteApprovals();

    /// @dev Modifier to restrict access to partyA.
    modifier onlyPartyA() {
        if (msg.sender != partyA) revert Unauthorized();
        _;
    }

    /// @dev Modifier to restrict access to partyB.
    modifier onlyPartyB() {
        if (msg.sender != partyB) revert Unauthorized();
        _;
    }

    /// @notice Constructor to set the parties involved in the escrow.
    /// @param _partyA The address of party A.
    /// @param _partyB The address of party B.
    constructor(address _partyA, address _partyB) {
        partyA = _partyA;
        partyB = _partyB;
    }

    /// @notice Allows a party to deposit funds into the escrow.
    /// @param amount The amount of funds to deposit.
    function depositFunds(uint256 amount) external payable {
        if (msg.value != amount) revert InsufficientFunds();
        funds += amount;
        emit FundsDeposited(amount);
    }

    /// @notice Allows a party to approve the transaction.
    function approveTransaction() external {
        if (msg.sender == partyA) {
            if (partyAApproved) revert AlreadyApproved();
            partyAApproved = true;
        } else if (msg.sender == partyB) {
            if (partyBApproved) revert AlreadyApproved();
            partyBApproved = true;
        } else {
            revert Unauthorized();
        }
        emit TransactionApproved(msg.sender);
    }

    /// @notice Releases funds to the designated recipient if both parties approve.
    function releaseFunds() external {
        if (!partyAApproved || !partyBApproved) revert IncompleteApprovals();
        uint256 amount = funds;
        funds = 0;
        payable(partyB).transfer(amount);
        emit FundsReleased(partyB);
    }

    /// @notice Refunds funds to the depositor if the transaction is not approved by both parties.
    function refundFunds() external {
        if (partyAApproved && partyBApproved) revert IncompleteApprovals();
        uint256 amount = funds;
        funds = 0;
        payable(partyA).transfer(amount);
        emit FundsRefunded(partyA);
    }
}
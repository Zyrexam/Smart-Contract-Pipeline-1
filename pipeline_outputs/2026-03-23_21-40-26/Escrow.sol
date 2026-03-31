// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Escrow Contract
/// @notice This contract holds funds until both parties approve the transaction.
contract Escrow {
    // State variables
    uint256 private funds;
    bool private partyAApproved;
    bool private partyBApproved;
    address private partyA;
    address private partyB;

    // Events
    event FundsDeposited(uint256 amount);
    event TransactionApproved(address party);
    event FundsReleased(uint256 amount);
    event FundsWithdrawn(uint256 amount);

    // Custom errors
    error NotAuthorized();
    error AlreadyApproved();
    error InsufficientFunds();
    error TransactionNotApproved();

    /// @notice Constructor to set the parties involved in the escrow
    /// @param _partyA Address of party A
    /// @param _partyB Address of party B
    constructor(address _partyA, address _partyB) {
        partyA = _partyA;
        partyB = _partyB;
    }

    /// @notice Allows a party to deposit funds into the escrow
    /// @param amount The amount to deposit
    function depositFunds(uint256 amount) external payable {
        if (msg.value != amount) revert InsufficientFunds();
        funds += amount;
        emit FundsDeposited(amount);
    }

    /// @notice Allows a party to approve the transaction
    function approveTransaction() external {
        if (msg.sender != partyA && msg.sender != partyB) revert NotAuthorized();
        if (msg.sender == partyA) {
            if (partyAApproved) revert AlreadyApproved();
            partyAApproved = true;
        } else if (msg.sender == partyB) {
            if (partyBApproved) revert AlreadyApproved();
            partyBApproved = true;
        }
        emit TransactionApproved(msg.sender);
    }

    /// @notice Releases funds to the designated party if both parties have approved
    function releaseFunds() external {
        if (!partyAApproved || !partyBApproved) revert TransactionNotApproved();
        uint256 amount = funds;
        funds = 0;
        payable(partyA).transfer(amount);
        emit FundsReleased(amount);
    }

    /// @notice Allows a party to withdraw funds if the transaction is not approved
    function withdrawFunds() external {
        if (partyAApproved && partyBApproved) revert TransactionNotApproved();
        uint256 amount = funds;
        funds = 0;
        payable(msg.sender).transfer(amount);
        emit FundsWithdrawn(amount);
    }
}
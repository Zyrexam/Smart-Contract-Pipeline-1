// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Escrow {
    // Mapping of transactions
    mapping (address => mapping (address => bool)) public transactions;

    // Mapping of funds
    mapping (address => mapping (address => uint256)) public funds;

    // Event emitted when funds are released
    event FundsReleased(address buyer, address seller, uint256 amount);

    // Event emitted when transaction is approved
    event TransactionApproved(address buyer, address seller);

    // Function to deposit funds into escrow
    function deposit(address buyer, address seller, uint256 amount) public {
        // Check if buyer and seller are different addresses
        require(buyer != seller, "Buyer and seller cannot be the same address");

        // Check if funds are being deposited for the first time
        require(funds[buyer][seller] == 0, "Funds already deposited");

        // Update funds mapping
        funds[buyer][seller] = amount;

        // Emit event to indicate funds have been deposited
        emit FundsDeposited(buyer, seller, amount);
    }

    // Function to approve transaction
    function approveTransaction(address buyer, address seller) public {
        // Check if buyer and seller are different addresses
        require(buyer != seller, "Buyer and seller cannot be the same address");

        // Check if funds have been deposited
        require(funds[buyer][seller] > 0, "Funds have not been deposited");

        // Update transactions mapping
        transactions[buyer][seller] = true;

        // Emit event to indicate transaction has been approved
        emit TransactionApproved(buyer, seller);
    }

    // Function to release funds
    function releaseFunds(address buyer, address seller) public {
        // Check if buyer and seller are different addresses
        require(buyer != seller, "Buyer and seller cannot be the same address");

        // Check if funds have been deposited
        require(funds[buyer][seller] > 0, "Funds have not been deposited");

        // Check if transaction has been approved
        require(transactions[buyer][seller], "Transaction has not been approved");

        // Transfer funds to buyer
        (bool sent, ) = payable(buyer).call{value: funds[buyer][seller]}("");
        require(sent, "Failed to send funds");

        // Update funds mapping
        funds[buyer][seller] = 0;

        // Emit event to indicate funds have been released
        emit FundsReleased(buyer, seller, funds[buyer][seller]);
    }

    // Event emitted when funds are deposited
    event FundsDeposited(address buyer, address seller, uint256 amount);
}
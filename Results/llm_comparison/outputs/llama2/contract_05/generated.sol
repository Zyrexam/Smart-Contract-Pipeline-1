// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Escrow {
    address public owner; // The address of the contract owner
    address public beneficiary; // The address of the beneficiary (party that will receive the funds)
    uint256 public amount; // The amount of funds held in escrow
    bool public approved; // A boolean indicating whether both parties have approved the transaction

    constructor() public {
        owner = msg.sender;
        beneficiary = address(0); // Initialize the beneficiary to the contract owner
        amount = 0; // Initialize the amount of funds held in escrow to 0
        approved = false; // Initialize the approved boolean to false
    }

    function approve(address _beneficiary) public {
        require(msg.sender == owner, "Only the contract owner can approve the transaction");
        beneficiary = _beneficiary;
        approved = true;
    }

    function release() public {
        require(approved, "The transaction has not been approved by both parties");
        amount = 0; // Release the funds to the beneficiary
    }
}
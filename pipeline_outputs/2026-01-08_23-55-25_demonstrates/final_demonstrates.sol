// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title UnprotectedVault
 * @dev VULNERABLE CONTRACT - DO NOT USE IN PRODUCTION
 * 
 * This contract demonstrates a missing Access Control vulnerability (SWC-105).
 * The withdrawAll function is public and lacks an onlyOwner check.
 */
contract UnprotectedVault {
    address public owner;

    error NotOwner();
    error InsufficientFunds();

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    receive() external payable {}

    // Fixed: Added onlyOwner modifier
    function withdrawAll() external onlyOwner {
        payable(msg.sender).transfer(address(this).balance);
    }
    
    // This one is protected correctly, for comparison
    function safeWithdraw(uint256 amount) external onlyOwner {
        if (address(this).balance < amount) revert InsufficientFunds();
        payable(msg.sender).transfer(amount);
    }
}
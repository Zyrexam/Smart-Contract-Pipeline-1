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

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    receive() external payable {}

    // VULNERABILITY: Missing onlyOwner modifier
    // Anyone can call this function and drain the contract
    function withdrawAll() external {
        // Should be: function withdrawAll() external onlyOwner {
        payable(msg.sender).transfer(address(this).balance);
    }
    
    // This one is protected correctly, for comparison
    function safeWithdraw(uint256 amount) external onlyOwner {
        require(address(this).balance >= amount, "Insufficient funds");
        payable(msg.sender).transfer(amount);
    }
}

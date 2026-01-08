// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ReentrancyGuard} from "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title ReentrancyBank
 * @dev Secure contract using ReentrancyGuard and checks-effects-interactions pattern
 */
contract ReentrancyBank is ReentrancyGuard {
    mapping(address => uint256) public balances;

    error NoBalance();
    error TransferFailed();

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() external nonReentrant {
        uint256 amount = balances[msg.sender];
        if (amount == 0) revert NoBalance();

        // State update before interaction
        balances[msg.sender] = 0;

        // Interaction
        (bool success, ) = msg.sender.call{value: amount}("");
        if (!success) revert TransferFailed();
    }
    
    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }
}
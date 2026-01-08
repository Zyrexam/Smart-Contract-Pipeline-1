// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ReentrancyBank
 * @dev VULNERABLE CONTRACT - DO NOT USE IN PRODUCTION
 * 
 * This contract demonstrates a classic Reentrancy vulnerability (SWC-107).
 * The withdraw function sends Ether before updating the balance.
 */
contract ReentrancyBank {
    mapping(address => uint256) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    // VULNERABILITY: External call before state update
    function withdraw() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "No balance");

        // Vulnerable line: Interaction before Effect
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        // State update happens too late
        balances[msg.sender] = 0;
    }
    
    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }
}

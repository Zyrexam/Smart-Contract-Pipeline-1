// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title PhishableWallet
 * @dev VULNERABLE CONTRACT - DO NOT USE IN PRODUCTION
 * 
 * This contract demonstrates improper authorization using tx.origin (SWC-115).
 * Attackers can trick the owner into calling a malicious contract that calls this wallet.
 */
contract PhishableWallet {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    receive() external payable {}

    // VULNERABILITY: Using tx.origin for authorization
    // Detection tools should flag this as a security risk
    function withdraw(address payable _recipient, uint256 _amount) public {
        require(tx.origin == owner, "Not authorized");
        
        // This allows a phishing attack if owner interacts with a malicious contract
        _recipient.transfer(_amount);
    }
    
    function setOwner(address _newOwner) public {
        // Also vulnerable
        require(tx.origin == owner, "Not authorized");
        owner = _newOwner;
    }
}

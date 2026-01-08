// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ReentrancyGuard} from "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title PhishableWallet
 * @dev Secure version of the contract with proper authorization and input validation
 */
contract PhishableWallet is ReentrancyGuard {
    address public owner;

    error NotAuthorized();
    error InvalidRecipient();
    error InsufficientBalance();

    constructor() {
        owner = msg.sender;
    }

    receive() external payable {}

    function withdraw(address payable _recipient, uint256 _amount) public nonReentrant {
        if (msg.sender != owner) revert NotAuthorized();
        if (_recipient == address(0)) revert InvalidRecipient();
        if (address(this).balance < _amount) revert InsufficientBalance();

        _recipient.transfer(_amount);
    }
    
    function setOwner(address _newOwner) public {
        if (msg.sender != owner) revert NotAuthorized();
        owner = _newOwner;
    }
}
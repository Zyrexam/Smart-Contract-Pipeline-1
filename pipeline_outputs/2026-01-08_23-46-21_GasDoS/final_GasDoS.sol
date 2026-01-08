// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ReentrancyGuard} from "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title GasDoS
 * @dev Denial of service by gas exhaustion in loop (SWC-113)
 */
contract GasDoS is ReentrancyGuard, Ownable {
    address[] public users;

    error TransferFailed(address user);

    function register() external {
        users.push(msg.sender);
    }

    function payout() external onlyOwner nonReentrant {
        uint256 length = users.length;
        for (uint256 i = 0; i < length; ++i) {
            (bool success, ) = payable(users[i]).call{value: 1 ether}("");
            if (!success) {
                revert TransferFailed(users[i]);
            }
        }
    }
}
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title GasDoS
 * @dev Denial of service by gas exhaustion in loop (SWC-113)
 */
contract GasDoS {
    address[] public users;

    function register() external {
        users.push(msg.sender);
    }

    function payout() external {
        // Malicious contract in users can always revert or use tons of gas
        for (uint256 i = 0; i < users.length; i++) {
            payable(users[i]).send(1 ether);
        }
    }
}
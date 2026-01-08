// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Overflow
 * @dev Fixed integer overflow by using Solidity ^0.8.20 which has built-in overflow checks
 */
contract Overflow {
    uint8 public count = 255;

    function increment() public {
        ++count; // Uses ++variable to save gas
    }
}
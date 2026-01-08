// SPDX-License-Identifier: MIT
pragma solidity ^0.7.6;

/**
 * @title Overflow
 * @dev Vulnerable to integer overflow (SWC-101) (<=0.7.x only)
 */
contract Overflow {
    uint8 public count = 255;

    function increment() public {
        count += 1; // Overflows to 0
    }
}
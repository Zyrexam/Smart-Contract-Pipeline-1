// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract BadStyle {
    uint256 private x; // fixed naming, added visibility

    function set(uint256 newX) public { // fixed function and variable naming
        x = newX;
    }
}
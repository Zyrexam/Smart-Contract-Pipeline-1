// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract UnusedVariables {
    uint256 public unusedState; // never used

    function calculate(uint256 x) public pure returns (uint256) {
        uint256 temp = x + 1; // unused local variable
        return x * 2;
    }
}

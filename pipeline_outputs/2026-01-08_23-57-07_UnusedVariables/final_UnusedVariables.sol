// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract UnusedVariables {
    function calculate(uint256 x) public pure returns (uint256) {
        return x * 2;
    }
}
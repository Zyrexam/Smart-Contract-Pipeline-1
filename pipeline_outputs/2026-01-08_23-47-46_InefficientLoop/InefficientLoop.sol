// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract InefficientLoop {
    function inefficient(uint256 n) public pure returns (uint256) {
        uint256 sum = 0;
        for (uint256 i = 0; i < n; i++) {
            sum += 1;
        }
        return sum;
    }
}

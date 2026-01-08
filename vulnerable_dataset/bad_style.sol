// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract bad_style {
    uint X; // bad naming, missing visibility

    function Set(uint _X) public {
        X = _X;
    }
}

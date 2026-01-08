// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract NoAccessControl {
    uint256 public adminValue;

    function updateAdminValue(uint256 _v) public {
        adminValue = _v;
    }
}

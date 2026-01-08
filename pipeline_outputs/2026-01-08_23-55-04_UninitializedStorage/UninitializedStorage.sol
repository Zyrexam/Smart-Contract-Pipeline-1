// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title UninitializedStorage
 * @dev Writes through uninitialized storage pointer (SWC-109)
 */
contract UninitializedStorage {
    struct Data { uint256 value; }
    Data public data;

    function write(uint256 _v) public {
        Data storage d;
        d.value = _v; // Overwrites storage[0] (likely the owner or critical data)
    }
}
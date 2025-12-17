// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Number Storage Contract
/// @notice This contract allows storing, updating, and retrieving a number.
/// @dev Implements a simple number storage with owner access control.
contract NumberStorage {
    uint256 private storedNumber;
    address private owner;

    /// @dev Emitted when the stored number is updated.
    /// @param updater The address of the user who updated the number.
    /// @param newNumber The new number that was stored.
    event NumberUpdated(address indexed updater, uint256 newNumber);

    /// @dev Custom error for unauthorized access.
    error NotOwner();

    /// @dev Sets the deployer as the initial owner of the contract.
    constructor() {
        owner = msg.sender;
    }

    /// @notice Updates the stored number to a new value provided by the user.
    /// @param newNumber The new number to store.
    /// @dev Only the owner can update the number.
    function updateNumber(uint256 newNumber) external onlyOwner {
        storedNumber = newNumber;
        emit NumberUpdated(msg.sender, newNumber);
    }

    /// @notice Retrieves the current stored number.
    /// @return The current stored number.
    function retrieveNumber() external view returns (uint256) {
        return storedNumber;
    }

    /// @dev Modifier to restrict access to the owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }
}
